"""
config.py
Centraliza todas as configurações, constantes e variáveis de ambiente do projeto.
Único ponto de acesso para parâmetros — facilita manutenção e testes.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Diretórios ──────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
OUTPUT_DIR  = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Arquivos ─────────────────────────────────────────────────────────────────
PLANILHA_PATH      = DATA_DIR / "clientes_TAG.xlsx"
RELATORIO_JSON     = OUTPUT_DIR / "relatorio.json"
RELATORIO_TXT      = OUTPUT_DIR / "relatorio.txt"

# ── API ──────────────────────────────────────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash-lite"
API_MAX_RETRIES    = 4
API_RETRY_DELAY    = 5.0   # segundos entre tentativas
API_TIMEOUT        = 30    # segundos

# ── Regras de classificação de risco ─────────────────────────────────────────
# Limites de exposição a ativos de risco (renda variável + cripto) por perfil
LIMITE_CONSERVADOR = 25.0   # até 25% em ativos de risco
LIMITE_MODERADO    = 55.0   # até 55% em ativos de risco
# acima de 55% → arrojado

# Limites de cripto por objetivo defensivo
CRIPTO_ALERTA_DEFENSIVO = 10.0   # % máximo tolerável em cripto para preservação/aposentadoria
CRIPTO_ALERTA_SEVERO    = 50.0   # % que gera alerta severo independente do perfil

# Soma de percentuais aceita como válida (tolerância de arredondamento)
SOMA_PERCENTUAL_TOLERANCIA = 1.0

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL  = logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
LOG_DATE   = "%H:%M:%S"

# ── Valores sentinela (dados ausentes) ───────────────────────────────────────
IDADE_DESCONHECIDA      = -1
PATRIMONIO_DESCONHECIDO = 0.0

# ── Objetivos válidos ────────────────────────────────────────────────────────
OBJETIVOS_VALIDOS = {"aposentadoria", "crescimento", "preservacao"}

# ── Colunas obrigatórias da planilha ─────────────────────────────────────────
COLUNAS_OBRIGATORIAS = [
    "nome",
    "idade",
    "patrimonio_total",
    "perc_renda_variavel",
    "perc_renda_fixa",
    "perc_cripto",
    "objetivo",
]
