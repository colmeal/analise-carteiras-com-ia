import json
import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from utils import get_logger
from config import BASE_DIR

logger = get_logger(__name__)

SERVICE_ACCOUNT_FILE = BASE_DIR / "credentials" / "tag-investimentos-api-3e63c4e18cdd.json"
RELATORIO_JSON_PATH  = BASE_DIR / "output" / "relatorio.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def exportar_para_sheets():
    try:
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )

        client = gspread.Client(auth=credentials)

        spreadsheet = client.open("Relatorio TAG Investimentos")

        worksheet = spreadsheet.sheet1

        worksheet.clear()

        headers = [
            "Nome",
            "Perfil",
            "Score",
            "Alertas",
            "Análise IA"
        ]

        worksheet.append_row(headers)
        
        with open(RELATORIO_JSON_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)

        for cliente in dados["clientes"]:
            worksheet.append_row([
                cliente.get("nome"),
                cliente.get("perfil_risco"),
                cliente.get("score_risco"),
                " | ".join(cliente.get("alertas", [])),
                cliente.get("resumo_ia")
            ])

        logger.info("✅ Dados enviados para Google Sheets!")

    except Exception as e:
        logger.error("Erro ao enviar para Google Sheets: %s", e)