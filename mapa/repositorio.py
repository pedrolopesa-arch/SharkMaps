"""Camada de dados do SharkMaps com validação geográfica, integridade, auditoria e backup."""

from datetime import datetime
from pathlib import Path
import shutil
from typing import Any, Dict, Optional, Tuple, Union
import uuid
import pandas as pd

import config

COLUNAS_PADRAO = config.COLUNAS_CSV


def validar_coordenadas(lat: float, lon: float) -> Tuple[bool, str]:
    """Valida se as coordenadas estão dentro dos limites do litoral de PE ou Fernando de Noronha."""
    lim_pe = config.LIMITES_LITORAL_PE
    lim_fn = config.LIMITES_NORONHA

    no_litoral_pe = (
        lim_pe["lat_min"] <= lat <= lim_pe["lat_max"]
        and lim_pe["lon_min"] <= lon <= lim_pe["lon_max"]
    )
    em_noronha = (
        lim_fn["lat_min"] <= lat <= lim_fn["lat_max"]
        and lim_fn["lon_min"] <= lon <= lim_fn["lon_max"]
    )

    if no_litoral_pe or em_noronha:
        return True, "Coordenadas válidas para a zona de monitoramento de Pernambuco."

    return False, (
        "Trava Geográfica Ativada: As coordenadas informadas estão fora da área de monitoramento "
        "de Pernambuco. O SharkMaps aceita apenas pontos no litoral pernambucano (lat -8.95 a -7.50, "
        "lon -35.25 a -34.75) ou no Arquipélago de Fernando de Noronha (lat -3.95 a -3.75, lon -32.55 a -32.35)."
    )


def verificar_duplicidade(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    data: str,
    nome: str,
    tolerancia_graus: float = 0.003
) -> bool:
    """Verifica se já existe registro com a mesma data e coordenadas muito próximas ou mesmo nome."""
    if df.empty:
        return False

    data_limpa = str(data).strip()
    if data_limpa:
        # Mesma data e proximidade espacial (< ~300 metros)
        mesma_data = df[df["data"].astype(str).str.strip() == data_limpa]
        if not mesma_data.empty:
            for _, r in mesma_data.iterrows():
                try:
                    r_lat = float(r["lat"])
                    r_lon = float(r["lon"])
                    if abs(r_lat - lat) <= tolerancia_graus and abs(r_lon - lon) <= tolerancia_graus:
                        return True
                except Exception:
                    continue

    # Mesmo nome exato no mesmo município/trecho
    nome_limpo = str(nome).strip().lower()
    if nome_limpo:
        nomes_existentes = df["nome"].astype(str).str.strip().str.lower()
        if (nomes_existentes == nome_limpo).any() and data_limpa:
            mesmo_nome_data = df[(nomes_existentes == nome_limpo) & (df["data"].astype(str).str.strip() == data_limpa)]
            if not mesmo_nome_data.empty:
                return True

    return False


def registrar_auditoria(usuario: str, acao: str, registro_id: str, detalhes: str) -> None:
    """Registra uma linha no log de auditoria institucional em dados/auditoria.log."""
    config.AUDITORIA_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] usuario={usuario} | acao={acao} | registro_id={registro_id} | detalhes={detalhes}\n"

    try:
        with open(config.AUDITORIA_LOG, "a", encoding="utf-8") as f:
            f.write(linha)
    except Exception as e:
        print(f"Erro ao gravar auditoria: {e}")


def gerar_backup_csv(caminho_csv: Union[str, Path]) -> Optional[Path]:
    """Cria uma cópia de backup do CSV com carimbo de data/hora em dados/backups/."""
    caminho_csv = Path(caminho_csv)
    if not caminho_csv.is_file():
        return None

    config.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = config.BACKUPS_DIR / f"pontos_backup_{timestamp}_{caminho_csv.name}"

    try:
        shutil.copy2(caminho_csv, destino)
        return destino
    except Exception as e:
        print(f"Erro ao gerar backup: {e}")
        return None


def carregar_pontos(
    caminho: Union[str, Path],
    apenas_oficiais: bool = False
) -> pd.DataFrame:
    """Lê o arquivo CSV de pontos, converte coordenadas para número e descarta linhas inválidas.

    Args:
        caminho: Caminho para o CSV.
        apenas_oficiais: Se True, filtra apenas registros com status='oficial'.

    Returns:
        pd.DataFrame padronizado.
    """
    caminho = Path(caminho)

    if not caminho.is_file() or caminho.stat().st_size == 0:
        return pd.DataFrame(columns=COLUNAS_PADRAO)

    try:
        df = pd.read_csv(caminho, encoding="utf-8", on_bad_lines="skip", dtype=str)
    except Exception:
        df = pd.read_csv(caminho, encoding="latin-1", on_bad_lines="skip", dtype=str)

    if "lat" not in df.columns or "lon" not in df.columns:
        return pd.DataFrame(columns=COLUNAS_PADRAO)

    df["lat"] = pd.to_numeric(
        df["lat"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )
    df["lon"] = pd.to_numeric(
        df["lon"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    df = df.dropna(subset=["lat", "lon"])

    for col in COLUNAS_PADRAO:
        if col not in df.columns:
            if col == "status":
                df[col] = "oficial"
            elif col == "id":
                df[col] = [f"PE-{i+1:03d}" for i in range(len(df))]
            else:
                df[col] = ""

    df["status"] = df["status"].fillna("oficial").str.strip().str.lower()
    df = df.fillna("")

    if apenas_oficiais:
        df = df[df["status"] == "oficial"]

    return df.reset_index(drop=True)


def adicionar_ponto(
    caminho: Union[str, Path],
    ponto: Dict[str, Any],
    usuario: Optional[str] = None
) -> Tuple[bool, str]:
    """Acrescenta um novo registro de ponto com validações geográficas e duplicação."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    try:
        lat = float(str(ponto.get("lat", 0)).replace(",", "."))
        lon = float(str(ponto.get("lon", 0)).replace(",", "."))
    except ValueError:
        return False, "Coordenadas numéricas inválidas."

    valido, msg_geo = validar_coordenadas(lat, lon)
    if not valido:
        return False, msg_geo

    df_atual = carregar_pontos(caminho, apenas_oficiais=False)
    if verificar_duplicidade(df_atual, lat, lon, str(ponto.get("data", "")), str(ponto.get("nome", ""))):
        return False, "Trava de Integridade: Já existe um registro cadastrado para esta mesma data e local aproximado."

    if caminho.is_file() and usuario:
        gerar_backup_csv(caminho)

    novo_id = ponto.get("id")
    if not novo_id:
        novo_id = f"PE-{len(df_atual) + 1:03d}"

    registro = {
        "id": novo_id,
        "tipo": str(ponto.get("tipo", "incidente")),
        "nome": str(ponto.get("nome", "")),
        "lat": lat,
        "lon": lon,
        "data": str(ponto.get("data", "")),
        "especie": str(ponto.get("especie", "")),
        "descricao": str(ponto.get("descricao", "")),
        "fonte": str(ponto.get("fonte", "")),
        "status": str(ponto.get("status", "oficial" if usuario else "pendente")),
    }

    novo_df = pd.DataFrame([registro])
    novo_df = novo_df[COLUNAS_PADRAO]

    arquivo_existe = caminho.is_file() and caminho.stat().st_size > 0
    novo_df.to_csv(
        caminho,
        mode="a",
        header=not arquivo_existe,
        index=False,
        encoding="utf-8"
    )

    if usuario:
        registrar_auditoria(usuario, "ADICIONAR", novo_id, f"Tipo={registro['tipo']}, Nome={registro['nome']}")
    else:
        registrar_auditoria("VISITANTE", "RELATO_PENDENTE", novo_id, f"Nome={registro['nome']}")

    return True, "Registro salvo com sucesso!"


def aprovar_ponto(caminho: Union[str, Path], registro_id: str, usuario: str) -> bool:
    """Aprova um relato de avistamento pendente, tornando-o oficial."""
    caminho = Path(caminho)
    df = carregar_pontos(caminho, apenas_oficiais=False)

    if df.empty or "id" not in df.columns:
        return False

    mascara = df["id"].astype(str) == str(registro_id)
    if not mascara.any():
        return False

    gerar_backup_csv(caminho)
    df.loc[mascara, "status"] = "oficial"
    df.to_csv(caminho, index=False, encoding="utf-8")

    registrar_auditoria(usuario, "APROVAR", str(registro_id), "Status alterado para oficial")
    return True


def excluir_ponto(caminho: Union[str, Path], registro_id: str, usuario: str) -> bool:
    """Exclui permanentemente um registro após gerar backup e gravar auditoria."""
    caminho = Path(caminho)
    df = carregar_pontos(caminho, apenas_oficiais=False)

    if df.empty or "id" not in df.columns:
        return False

    mascara = df["id"].astype(str) == str(registro_id)
    if not mascara.any():
        return False

    gerar_backup_csv(caminho)
    df_novo = df[~mascara]
    df_novo.to_csv(caminho, index=False, encoding="utf-8")

    registrar_auditoria(usuario, "EXCLUIR", str(registro_id), "Registro removido da base")
    return True


def editar_ponto(
    caminho: Union[str, Path],
    registro_id: str,
    novos_dados: Dict[str, Any],
    usuario: str
) -> Tuple[bool, str]:
    """Atualiza os campos de um registro existente com validação e auditoria."""
    caminho = Path(caminho)
    df = carregar_pontos(caminho, apenas_oficiais=False)

    mascara = df["id"].astype(str) == str(registro_id)
    if not mascara.any():
        return False, "Registro não encontrado."

    lat = float(novos_dados.get("lat", df.loc[mascara, "lat"].values[0]))
    lon = float(novos_dados.get("lon", df.loc[mascara, "lon"].values[0]))
    valido, msg = validar_coordenadas(lat, lon)
    if not valido:
        return False, msg

    gerar_backup_csv(caminho)

    for campo in COLUNAS_PADRAO:
        if campo in novos_dados and campo != "id":
            df.loc[mascara, campo] = novos_dados[campo]

    df.to_csv(caminho, index=False, encoding="utf-8")
    registrar_auditoria(usuario, "EDITAR", str(registro_id), f"Campos={list(novos_dados.keys())}")
    return True, "Registro atualizado com sucesso!"


def exportar_csv(caminho_origem: Union[str, Path], caminho_destino: Union[str, Path], usuario: str) -> bool:
    """Exporta a base de dados de pontos com registro de auditoria."""
    try:
        shutil.copy2(caminho_origem, caminho_destino)
        registrar_auditoria(usuario, "EXPORTAR_CSV", "TODOS", f"Destino={caminho_destino}")
        return True
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")
        return False
