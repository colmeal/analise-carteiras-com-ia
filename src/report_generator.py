"""
report_generator.py
Gera os relatórios finais em formato JSON (estruturado) e TXT (legível).
Separado do processamento para facilitar extensão futura
(ex: adicionar PDF, e-mail, Google Sheets).
"""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
from utils import get_logger, formatar_moeda, formatar_percentual
from validator import Inconsistencia
from risk_classifier import ResultadoClassificacao
from config import RELATORIO_JSON, RELATORIO_TXT, IDADE_DESCONHECIDA

logger = get_logger(__name__)

SEPARADOR = "═" * 60
SEP_FINO  = "─" * 60


def _montar_registro(
    cliente: dict,
    classificacao: ResultadoClassificacao,
    analise_ia: str,
) -> dict:
    """Monta o dicionário de um cliente para o relatório JSON."""
    return {
        "nome":                  cliente["nome"],
        "idade":                 int(cliente["idade"]) if int(cliente["idade"]) != IDADE_DESCONHECIDA else None,
        "patrimonio_total":      float(cliente["patrimonio_total"]),
        "alocacao": {
            "renda_variavel_pct": float(cliente["perc_renda_variavel"]),
            "renda_fixa_pct":     float(cliente["perc_renda_fixa"]),
            "cripto_pct":         float(cliente["perc_cripto"]),
        },
        "objetivo":              cliente["objetivo"],
        "perfil_risco":          classificacao.perfil,
        "score_risco":           classificacao.score,
        "justificativa":         classificacao.justificativa,
        "alertas":               classificacao.alertas,
        "resumo_ia":             analise_ia,
        "status":                "ALERTA" if classificacao.alertas else "OK",
    }


def gerar_relatorio_json(
    registros: list[dict],
    inconsistencias: list[Inconsistencia],
    caminho: Path = RELATORIO_JSON,
) -> None:
    """Salva o relatório estruturado em JSON."""
    payload = {
        "meta": {
            "gerado_em":            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_clientes":       len(registros),
            "clientes_com_alerta":  sum(1 for r in registros if r["status"] == "ALERTA"),
            "total_inconsistencias": len(inconsistencias),
        },
        "inconsistencias_nos_dados": [
            {
                "cliente":   i.cliente,
                "campo":     i.campo,
                "tipo":      i.tipo,
                "descricao": i.descricao,
                "decisao":   i.decisao,
            }
            for i in inconsistencias
        ],
        "clientes": registros,
    }

    try:
        caminho.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info("Relatório JSON salvo: %s", caminho)
    except Exception as exc:
        raise RuntimeError(f"Erro ao salvar relatório JSON: {exc}") from exc


def gerar_relatorio_txt(
    registros: list[dict],
    inconsistencias: list[Inconsistencia],
    caminho: Path = RELATORIO_TXT,
) -> None:
    """Salva o relatório em formato texto legível."""
    linhas: list[str] = []

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    linhas += [
        SEPARADOR,
        "  TAG INVESTIMENTOS — RELATÓRIO DE ANÁLISE DE CARTEIRAS",
        f"  Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        f"  Total de clientes: {len(registros)}  |  "
        f"Com alerta: {sum(1 for r in registros if r['status'] == 'ALERTA')}",
        SEPARADOR, "",
    ]

    # ── Inconsistências nos dados ──────────────────────────────────────────────
    if inconsistencias:
        linhas += [
            "⚠  INCONSISTÊNCIAS DETECTADAS NOS DADOS",
            SEP_FINO,
        ]
        for inc in inconsistencias:
            linhas += [
                f"  Cliente : {inc.cliente}",
                f"  Campo   : {inc.campo}  ({inc.tipo})",
                f"  Problema: {inc.descricao}",
                f"  Decisão : {inc.decisao}",
                "",
            ]
        linhas += [SEPARADOR, ""]

    # ── Análise por cliente ───────────────────────────────────────────────────
    linhas.append("  ANÁLISE POR CLIENTE")
    linhas.append(SEPARADOR)

    for i, r in enumerate(registros, 1):
        idade_str = str(r["idade"]) + " anos" if r["idade"] else "não informada"
        patrimonio_str = formatar_moeda(r["patrimonio_total"]) if r["patrimonio_total"] else "não informado"
        status_icon = "⚠" if r["status"] == "ALERTA" else "✓"

        linhas += [
            "",
            f"{status_icon}  [{i:02d}] {r['nome']}",
            SEP_FINO,
            f"  Idade          : {idade_str}",
            f"  Patrimônio     : {patrimonio_str}",
            f"  Objetivo       : {r['objetivo']}",
            f"  Alocação       : {formatar_percentual(r['alocacao']['renda_variavel_pct'])} var. | "
            f"{formatar_percentual(r['alocacao']['renda_fixa_pct'])} fixa | "
            f"{formatar_percentual(r['alocacao']['cripto_pct'])} cripto",
            f"  Perfil de risco: {r['perfil_risco'].upper()}  (score: {r['score_risco']}/100)",
            f"  Status         : {r['status']}",
        ]

        if r["alertas"]:
            linhas.append("  Alertas:")
            for alerta in r["alertas"]:
                linhas.append(f"    • {alerta}")

        linhas += [
            "",
            "  Análise (IA):",
        ]
        for paragrafo in r["resumo_ia"].split("\n"):
            if paragrafo.strip():
                linhas.append(f"  {paragrafo.strip()}")

    linhas += ["", SEPARADOR, "  FIM DO RELATÓRIO", SEPARADOR]

    try:
        caminho.write_text("\n".join(linhas), encoding="utf-8")
        logger.info("Relatório TXT salvo: %s", caminho)
    except Exception as exc:
        raise RuntimeError(f"Erro ao salvar relatório TXT: {exc}") from exc
