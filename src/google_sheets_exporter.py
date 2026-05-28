import json
import gspread
from google.oauth2.service_account import Credentials
from utils import get_logger

logger = get_logger(__name__)

SERVICE_ACCOUNT_FILE = "../credentials/tag-investimentos-api-3e63c4e18cdd.json"

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

        client = gspread.authorize(credentials)

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
        
        with open("../output/relatorio.json", "r", encoding="utf-8") as f:
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