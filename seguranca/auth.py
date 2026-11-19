"""Módulo de autenticação institucional, hash criptográfico e gestão de acessos."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import secrets
from typing import Any, Dict, List, Optional, Tuple

import config

CAMINHO_ADMINS = config.BASE_DIR / "dados" / "admins.json"

DOMINIOS_AUTORIZADOS = (
    "@ufrpe.br",
    "@ufpe.br",
    "@upe.br",
    "@pe.gov.br",
    "@cemit.pe.gov.br",
    "@bombeiros.pe.gov.br",
    "@ibama.gov.br",
    "@icmbio.gov.br",
    "@gov.br",
)


def _gerar_salt() -> str:
    """Gera um salt criptográfico aleatório e seguro."""
    return secrets.token_hex(16)


def _calcular_hash(senha: str, salt: str) -> str:
    """Calcula o hash SHA-256 combinando a senha e o salt."""
    conteudo = (salt + senha).encode("utf-8")
    return hashlib.sha256(conteudo).hexdigest()


def inicializar_admins_se_necessario() -> None:
    """Inicializa a base institucional de administradores se o arquivo não existir."""
    CAMINHO_ADMINS.parent.mkdir(parents=True, exist_ok=True)

    if not CAMINHO_ADMINS.is_file() or CAMINHO_ADMINS.stat().st_size == 0:
        salt_super = _gerar_salt()
        hash_super = _calcular_hash("SharkUFRPE@2026", salt_super)

        salt_cemit = _gerar_salt()
        hash_cemit = _calcular_hash("SharkUFRPE@2026", salt_cemit)

        agora = datetime.now().isoformat()
        dados_iniciais = {
            "admin": {
                "nome": "Super-Administrador do Sistema",
                "instituicao": "UFRPE / Projeto SharkMaps",
                "email": "admin@ufrpe.br",
                "papel": "superadmin",
                "salt": salt_super,
                "hash": hash_super,
                "ativo": True,
                "criado_em": agora,
            },
            "admin_cemit": {
                "nome": "Comitê Estadual de Monitoramento de Incidentes com Tubarões",
                "instituicao": "CEMIT - Pernambuco",
                "email": "contato.cemit@pe.gov.br",
                "papel": "pesquisador",
                "salt": salt_cemit,
                "hash": hash_cemit,
                "ativo": True,
                "criado_em": agora,
            },
        }

        with open(CAMINHO_ADMINS, "w", encoding="utf-8") as f:
            json.dump(dados_iniciais, f, indent=4, ensure_ascii=False)


def _carregar_usuarios() -> Dict[str, Any]:
    inicializar_admins_se_necessario()
    try:
        with open(CAMINHO_ADMINS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _salvar_usuarios(usuarios: Dict[str, Any]) -> None:
    CAMINHO_ADMINS.parent.mkdir(parents=True, exist_ok=True)
    with open(CAMINHO_ADMINS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


def verificar_credenciais(usuario: str, senha: str) -> Optional[Dict[str, Any]]:
    """Verifica usuário e senha contra a base criptografada.

    Retorna os dados do usuário (sem salt/hash) se válido e ativo, ou None.
    """
    usuarios = _carregar_usuarios()
    usuario_normalizado = usuario.strip().lower()

    if usuario_normalizado not in usuarios:
        return None

    dados = usuarios[usuario_normalizado]
    if not dados.get("ativo", True):
        return None

    salt = dados.get("salt", "")
    hash_esperado = dados.get("hash", "")
    hash_calculado = _calcular_hash(senha, salt)

    if secrets.compare_digest(hash_calculado, hash_esperado):
        return {
            "usuario": usuario_normalizado,
            "nome": dados.get("nome", ""),
            "instituicao": dados.get("instituicao", ""),
            "email": dados.get("email", ""),
            "papel": dados.get("papel", "pesquisador"),
        }
    return None


def trocar_senha(usuario: str, senha_atual: str, nova_senha: str) -> Tuple[bool, str]:
    """Altera a senha de um usuário autenticado."""
    if len(nova_senha) < 8:
        return False, "A nova senha deve ter pelo menos 8 caracteres."

    usuarios = _carregar_usuarios()
    usuario_normalizado = usuario.strip().lower()

    if usuario_normalizado not in usuarios:
        return False, "Usuário não encontrado."

    dados = usuarios[usuario_normalizado]
    salt = dados.get("salt", "")
    hash_esperado = dados.get("hash", "")

    if not secrets.compare_digest(_calcular_hash(senha_atual, salt), hash_esperado):
        return False, "Senha atual incorreta."

    novo_salt = _gerar_salt()
    novo_hash = _calcular_hash(nova_senha, novo_salt)
    dados["salt"] = novo_salt
    dados["hash"] = novo_hash
    dados["atualizado_em"] = datetime.now().isoformat()

    _salvar_usuarios(usuarios)
    return True, "Senha alterada com sucesso!"


def validar_email_institucional(email: str) -> bool:
    """Verifica se o e-mail pertence aos domínios acadêmicos ou oficiais credenciados."""
    email_limpo = email.strip().lower()
    return any(email_limpo.endswith(dom) for dom in DOMINIOS_AUTORIZADOS)


def cadastrar_pesquisador(
    solicitante: str,
    novo_usuario: str,
    senha_inicial: str,
    nome: str,
    instituicao_matricula: str,
    email: str,
    papel: str = "pesquisador",
) -> Tuple[bool, str]:
    """Cadastra um novo pesquisador/moderador no sistema (exclusivo para Super-Admin)."""
    usuarios = _carregar_usuarios()
    solicitante_norm = solicitante.strip().lower()

    if solicitante_norm not in usuarios or usuarios[solicitante_norm].get("papel") != "superadmin":
        return False, "Permissão negada. Apenas Super-Administradores podem credenciar pesquisadores."

    usuario_norm = re.sub(r"[^a-zA-Z0-9_.-]", "", novo_usuario.strip().lower())
    if not usuario_norm or len(usuario_norm) < 3:
        return False, "Identificador de usuário inválido (mínimo de 3 caracteres alfanuméricos)."

    if usuario_norm in usuarios:
        return False, f"O usuário '{usuario_norm}' já está cadastrado no sistema."

    if len(senha_inicial) < 8:
        return False, "A senha inicial deve possuir no mínimo 8 caracteres."

    if not validar_email_institucional(email):
        return False, (
            "E-mail institucional inválido. É obrigatório utilizar domínio acadêmico ou oficial "
            "(@ufrpe.br, @ufpe.br, @upe.br ou órgãos governamentais autorizados)."
        )

    salt = _gerar_salt()
    hash_senha = _calcular_hash(senha_inicial, salt)

    usuarios[usuario_norm] = {
        "nome": nome.strip(),
        "instituicao": instituicao_matricula.strip(),
        "email": email.strip().lower(),
        "papel": papel if papel in ("pesquisador", "superadmin") else "pesquisador",
        "salt": salt,
        "hash": hash_senha,
        "ativo": True,
        "criado_por": solicitante_norm,
        "criado_em": datetime.now().isoformat(),
    }

    _salvar_usuarios(usuarios)
    return True, f"Pesquisador '{usuario_norm}' cadastrado com sucesso!"


def alternar_status_usuario(solicitante: str, usuario_alvo: str, ativo: bool) -> Tuple[bool, str]:
    """Ativa ou desativa o acesso de um pesquisador."""
    usuarios = _carregar_usuarios()
    solicitante_norm = solicitante.strip().lower()
    alvo_norm = usuario_alvo.strip().lower()

    if solicitante_norm not in usuarios or usuarios[solicitante_norm].get("papel") != "superadmin":
        return False, "Permissão negada. Apenas Super-Administradores podem gerenciar acessos."

    if alvo_norm == solicitante_norm:
        return False, "Não é permitido desativar a própria conta de Super-Administrador."

    if alvo_norm not in usuarios:
        return False, "Usuário alvo não encontrado."

    usuarios[alvo_norm]["ativo"] = bool(ativo)
    _salvar_usuarios(usuarios)
    status_str = "ativado" if ativo else "desativado"
    return True, f"Usuário '{alvo_norm}' {status_str} com sucesso!"


def listar_usuarios(solicitante: str) -> List[Dict[str, Any]]:
    """Retorna a lista de usuários sem dados sensíveis (para o painel de gestão)."""
    usuarios = _carregar_usuarios()
    solicitante_norm = solicitante.strip().lower()

    if solicitante_norm not in usuarios or usuarios[solicitante_norm].get("papel") != "superadmin":
        return []

    resultado = []
    for user_id, dados in usuarios.items():
        resultado.append({
            "usuario": user_id,
            "nome": dados.get("nome", ""),
            "instituicao": dados.get("instituicao", ""),
            "email": dados.get("email", ""),
            "papel": dados.get("papel", "pesquisador"),
            "ativo": dados.get("ativo", True),
            "criado_em": dados.get("criado_em", "")[:10],
        })
    return resultado
