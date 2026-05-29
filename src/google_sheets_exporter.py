import json
import gspread
from google.oauth2.service_account import Credentials
from utils import get_logger
from config import BASE_DIR

logger = get_logger(__name__)

SERVICE_ACCOUNT_FILE = BASE_DIR / "credentials" / "service_account.json"
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

        # Inicialização com o método recomendado da biblioteca
        client = gspread.authorize(credentials)

        spreadsheet = client.open("Relatorio Analise Carteiras IA")
        worksheet = spreadsheet.sheet1

        headers = [
            "Nome",
            "Perfil",
            "Score",
            "Alertas",
            "Análise IA",
        ]

        # Estrutura a matriz completa na memória
        linhas = [headers]
        
        with open(RELATORIO_JSON_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)

        for cliente in dados["clientes"]:
            linhas.append([
                cliente.get("nome"),
                cliente.get("perfil_risco"),
                cliente.get("score_risco"),
                " | ".join(cliente.get("alertas", [])),
                cliente.get("resumo_ia"),
            ])

        # Pipeline Idempotente: Garante reexecução segura sem quebras ou duplicidade
        if len(linhas) > 1:
            worksheet.clear()
            worksheet.append_rows(linhas, value_input_option="USER_ENTERED")

        logger.info("✅ Dados enviados para Google Sheets com sucesso!")

    except Exception as exc:
        logger.error("Erro ao enviar para Google Sheets: %s", exc)
        raise RuntimeError(f"Falha na exportação para Google Sheets: {exc}") from exc