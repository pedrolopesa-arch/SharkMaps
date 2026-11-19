"""Configurações e caminhos globais do SharkMaps."""

from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"
CONTEUDO_DIR = BASE_DIR / "conteudo"
IMAGENS_DIR = CONTEUDO_DIR / "imagens"

# Arquivo de dados de pontos
PONTOS_CSV = DADOS_DIR / "pontos.csv"

# Colunas padrão do repositório
COLUNAS_CSV = [
    "tipo",
    "nome",
    "lat",
    "lon",
    "data",
    "especie",
    "descricao",
    "fonte"
]
