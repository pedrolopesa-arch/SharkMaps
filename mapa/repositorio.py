"""Camada de dados do SharkMaps: leitura e persistência de pontos georreferenciados."""

from pathlib import Path
from typing import Any, Dict, Union
import pandas as pd

COLUNAS_PADRAO = [
    "tipo",
    "nome",
    "lat",
    "lon",
    "data",
    "especie",
    "descricao",
    "fonte"
]


def carregar_pontos(caminho: Union[str, Path]) -> pd.DataFrame:
    """Lê o arquivo CSV de pontos, converte coordenadas para número e descarta linhas inválidas.

    Args:
        caminho: Caminho (str ou Path) para o arquivo CSV.

    Returns:
        pd.DataFrame com os pontos válidos e colunas padronizadas.
    """
    caminho = Path(caminho)

    if not caminho.is_file() or caminho.stat().st_size == 0:
        return pd.DataFrame(columns=COLUNAS_PADRAO)

    try:
        df = pd.read_csv(caminho, encoding="utf-8", on_bad_lines="skip")
    except Exception:
        # Fallback de encoding caso o arquivo tenha sido salvo com charset latin-1/windows-1252
        df = pd.read_csv(caminho, encoding="latin-1", on_bad_lines="skip")

    # Garante que as colunas essenciais de coordenadas existam
    if "lat" not in df.columns or "lon" not in df.columns:
        return pd.DataFrame(columns=COLUNAS_PADRAO)

    # Converte lat e lon para numérico, tratando vírgulas como ponto decimal
    df["lat"] = pd.to_numeric(
        df["lat"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )
    df["lon"] = pd.to_numeric(
        df["lon"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # Descarta linhas onde latitude ou longitude são inválidas/nulas
    df = df.dropna(subset=["lat", "lon"])

    # Garante a presença de todas as colunas padrão
    for col in COLUNAS_PADRAO:
        if col not in df.columns:
            df[col] = ""

    # Preenche valores NaN nas colunas textuais
    df = df.fillna("")

    return df.reset_index(drop=True)


def adicionar_ponto(caminho: Union[str, Path], ponto: Dict[str, Any]) -> None:
    """Acrescenta um novo registro de ponto ao arquivo CSV.

    Se o arquivo já existir, adapta o registro ao cabeçalho existente.
    Caso contrário, cria o arquivo com as colunas padrão.

    Args:
        caminho: Caminho (str ou Path) para o arquivo CSV.
        ponto: Dicionário contendo os dados do ponto a ser adicionado.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    arquivo_existe = caminho.is_file() and caminho.stat().st_size > 0

    if arquivo_existe:
        try:
            header_cols = list(pd.read_csv(caminho, nrows=0).columns)
        except Exception:
            header_cols = COLUNAS_PADRAO
    else:
        header_cols = COLUNAS_PADRAO

    novo_df = pd.DataFrame([ponto])

    # Garante que todas as colunas esperadas existam
    for col in header_cols:
        if col not in novo_df.columns:
            novo_df[col] = ""

    novo_df = novo_df[header_cols]

    novo_df.to_csv(
        caminho,
        mode="a",
        header=not arquivo_existe,
        index=False,
        encoding="utf-8"
    )
