"""Configurações globais, caminhos e regras de integridade do SharkMaps."""

from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"
CONTEUDO_DIR = BASE_DIR / "conteudo"
IMAGENS_DIR = CONTEUDO_DIR / "imagens"
ASSETS_DIR = BASE_DIR / "assets"
CAMADAS_DIR = DADOS_DIR / "camadas"
BACKUPS_DIR = DADOS_DIR / "backups"

# Arquivos de dados e auditoria
PONTOS_CSV = DADOS_DIR / "pontos.csv"
AREAS_PERIGO_GEOJSON = CAMADAS_DIR / "areas_perigo.geojson"
AUDITORIA_LOG = DADOS_DIR / "auditoria.log"
ADMINS_JSON = DADOS_DIR / "admins.json"
LOGO_SVG = ASSETS_DIR / "logo_sharkmaps.svg"

# Colunas padrão do repositório de pontos georreferenciados
COLUNAS_CSV = [
    "id",
    "tipo",
    "nome",
    "lat",
    "lon",
    "data",
    "especie",
    "descricao",
    "fonte",
    "status"
]

# Delimitação geográfica aceita pelo sistema (Trava Geográfica)
LIMITES_LITORAL_PE = {
    "lat_min": -8.95,
    "lat_max": -7.50,
    "lon_min": -35.25,
    "lon_max": -34.75,
}

LIMITES_NORONHA = {
    "lat_min": -3.95,
    "lat_max": -3.75,
    "lon_min": -32.55,
    "lon_max": -32.35,
}
