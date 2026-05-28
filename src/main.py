"""
main.py
Ponto de entrada do projeto TAG Investimentos — Desafio Técnico.
Orquestra o pipeline completo: leitura → validação → classificação → IA → relatório.
"""

import sys
from google_sheets_exporter import exportar_para_sheets
from utils import get_logger
from config import PLANILHA_PATH
from data_loader import carregar_planilha
from validator import validar_e_normalizar
from risk_classifier import classificar
from ai_analyzer import configurar_cliente, analisar_com_ia
from report_generator import (
    _montar_registro,
    gerar_relatorio_json,
    gerar_relatorio_txt,
)

logger = get_logger(__name__)


def main() -> None:
    logger.info("=" * 55)
    logger.info("  TAG Investimentos — Análise de Carteiras")
    logger.info("=" * 55)

    logger.info("[1/4] Lendo planilha...")
    try:
        df_bruto = carregar_planilha(PLANILHA_PATH)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        logger.critical("Falha na leitura: %s", exc)
        sys.exit(1)

    logger.info("[2/4] Validando e normalizando dados...")
    resultado_validacao = validar_e_normalizar(df_bruto)
    df = resultado_validacao.df

    logger.info("[3/4] Conectando à API Gemini...")
    try:
        model = configurar_cliente()
    except EnvironmentError as exc:
        logger.critical("Falha na configuração da API: %s", exc)
        sys.exit(1)

    logger.info("[4/4] Processando %d clientes...", len(df))
    registros: list[dict] = []

    for _, row in df.iterrows():
        cliente = row.to_dict()
        nome = cliente.get("nome", "Desconhecido")

        logger.info("  → %s", nome)

        classificacao = classificar(cliente)
        analise = analisar_com_ia(
            model=model,
            cliente=cliente,
            perfil=classificacao.perfil,
            score=classificacao.score,
            alertas=classificacao.alertas,
            justificativa=classificacao.justificativa,
        )

        registros.append(_montar_registro(cliente, classificacao, analise))

    logger.info("Gerando relatórios...")
    try:
        gerar_relatorio_json(registros, resultado_validacao.inconsistencias)
        gerar_relatorio_txt(registros, resultado_validacao.inconsistencias)
        exportar_para_sheets()
    except RuntimeError as exc:
        logger.error("Erro ao salvar relatórios: %s", exc)
        sys.exit(1)

    alertas_total = sum(1 for r in registros if r["status"] == "ALERTA")

    logger.info("=" * 55)
    logger.info("Concluído!")
    logger.info("  Clientes processados : %d", len(registros))
    logger.info("  Com alertas          : %d", alertas_total)
    logger.info("  Inconsistências      : %d", resultado_validacao.total_inconsistencias)
    logger.info("  Relatórios em        : output/")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()