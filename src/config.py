"""Configurações compartilhadas pelos scripts do projeto."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS_BRUTOS = RAIZ / "data" / "raw"
DADOS_EXTERNOS = RAIZ / "data" / "external"
DADOS_PROCESSADOS = RAIZ / "data" / "processed"
FIGURAS = RAIZ / "outputs" / "figures"
TABELAS = RAIZ / "outputs" / "tables"

# Repositório do TCC de onde vêm os dados, fixado em um commit para que a
# análise seja reprodutível mesmo que o repositório original mude.
TCC_REPO = "AlvesLuan/tcc_scraper_sofascore"
TCC_COMMIT = "23af40d2f9eab3cf861891d6d89f492b36dfefbc"
ARQUIVOS_TCC = [
    "todos-base_detalhada_geral_publico.csv",
    "z4-todos-base_detalhada_geral_publico.csv",
]

CLASSIFICACAO = DADOS_EXTERNOS / "classificacao_final_2020_2025.csv"
BASE_PROCESSADA = DADOS_PROCESSADOS / "partidas_disputa_titulo.csv"

# Campeão (C) e vice-campeão (V) de cada temporada analisada.
CAMPANHAS = {
    (2020, "Flamengo"): "Campeão",
    (2020, "Internacional"): "Vice",
    (2021, "Atlético Mineiro"): "Campeão",
    (2021, "Flamengo"): "Vice",
    (2022, "Palmeiras"): "Campeão",
    (2022, "Internacional"): "Vice",
    (2023, "Palmeiras"): "Campeão",
    (2023, "Grêmio"): "Vice",
    (2024, "Botafogo"): "Campeão",
    (2024, "Palmeiras"): "Vice",
    (2025, "Flamengo"): "Campeão",
    (2025, "Palmeiras"): "Vice",
}

# Variáveis usadas como preditoras nos modelos.
PREDITORAS = [
    "mandante",
    "posicao_adv",
    "forma_recente",
    "dif_idade",
    "dif_altura",
    "rodada",
    "meio_semana",
    "hora",
    "campeao",
]

SEMENTE = 42

# Cores das séries (paleta categórica validada: azul e laranja).
COR_CAMPEAO = "#2a78d6"
COR_VICE = "#eb6834"
