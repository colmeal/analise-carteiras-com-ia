"""
validator.py
Valida e normaliza os dados dos clientes.
Cada inconsistência é registrada com tipo, descrição e decisão tomada.
Separado do data_loader para respeitar o princípio de responsabilidade única.
"""

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
from utils import get_logger
from config import (
    OBJETIVOS_VALIDOS,
    SOMA_PERCENTUAL_TOLERANCIA,
    IDADE_DESCONHECIDA,
    PATRIMONIO_DESCONHECIDO,
)

logger = get_logger(__name__)


@dataclass
class Inconsistencia:
    """Representa uma inconsistência detectada nos dados de um cliente."""
    cliente:   str
    campo:     str
    tipo:      str
    descricao: str
    decisao:   str


@dataclass
class ResultadoValidacao:
    """Resultado completo da etapa de validação."""
    df:              pd.DataFrame
    inconsistencias: list[Inconsistencia] = field(default_factory=list)

    @property
    def total_inconsistencias(self) -> int:
        return len(self.inconsistencias)


def validar_e_normalizar(df: pd.DataFrame) -> ResultadoValidacao:
    """
    Valida e normaliza o DataFrame de clientes.
    Trata cada inconsistência de forma explícita e registra a decisão tomada.

    Args:
        df: DataFrame bruto lido da planilha

    Returns:
        ResultadoValidacao com DataFrame tratado e lista de inconsistências
    """
    df = df.copy()
    inconsistencias: list[Inconsistencia] = []

    for idx, row in df.iterrows():
        nome = str(row.get("nome", f"Linha {idx + 2}")).strip()

        # ── Idade ────────────────────────────────────────────────────────────
        if pd.isna(row["idade"]):
            inconsistencias.append(Inconsistencia(
                cliente=nome, campo="idade", tipo="valor_nulo",
                descricao="Idade não informada.",
                decisao=f"Substituída por sentinela {IDADE_DESCONHECIDA}. "
                        "Classificação de risco pode ser imprecisa."
            ))
            df.at[idx, "idade"] = IDADE_DESCONHECIDA
        else:
            try:
                df.at[idx, "idade"] = int(float(row["idade"]))
            except (ValueError, TypeError):
                inconsistencias.append(Inconsistencia(
                    cliente=nome, campo="idade", tipo="tipo_invalido",
                    descricao=f"Valor de idade não numérico: '{row['idade']}'.",
                    decisao=f"Substituído por {IDADE_DESCONHECIDA}."
                ))
                df.at[idx, "idade"] = IDADE_DESCONHECIDA

        # ── Patrimônio ───────────────────────────────────────────────────────
        if pd.isna(row["patrimonio_total"]):
            inconsistencias.append(Inconsistencia(
                cliente=nome, campo="patrimonio_total", tipo="valor_nulo",
                descricao="Patrimônio total não informado.",
                decisao="Assumido como R$ 0. Análise de IA indicará a ausência do dado."
            ))
            df.at[idx, "patrimonio_total"] = PATRIMONIO_DESCONHECIDO
        else:
            try:
                df.at[idx, "patrimonio_total"] = float(row["patrimonio_total"])
            except (ValueError, TypeError):
                inconsistencias.append(Inconsistencia(
                    cliente=nome, campo="patrimonio_total", tipo="tipo_invalido",
                    descricao=f"Patrimônio não numérico: '{row['patrimonio_total']}'.",
                    decisao="Assumido como R$ 0."
                ))
                df.at[idx, "patrimonio_total"] = PATRIMONIO_DESCONHECIDO

        # ── Percentuais de alocação ──────────────────────────────────────────
        for col in ["perc_renda_variavel", "perc_renda_fixa", "perc_cripto"]:
            if pd.isna(row[col]):
                inconsistencias.append(Inconsistencia(
                    cliente=nome, campo=col, tipo="valor_nulo",
                    descricao=f"Campo '{col}' não informado.",
                    decisao="Assumido como 0%."
                ))
                df.at[idx, col] = 0.0
            else:
                try:
                    df.at[idx, col] = float(row[col])
                except (ValueError, TypeError):
                    inconsistencias.append(Inconsistencia(
                        cliente=nome, campo=col, tipo="tipo_invalido",
                        descricao=f"Valor não numérico em '{col}': '{row[col]}'.",
                        decisao="Assumido como 0%."
                    ))
                    df.at[idx, col] = 0.0

        # ── Soma dos percentuais ─────────────────────────────────────────────
        soma = (
            float(df.at[idx, "perc_renda_variavel"])
            + float(df.at[idx, "perc_renda_fixa"])
            + float(df.at[idx, "perc_cripto"])
        )
        if abs(soma - 100.0) > SOMA_PERCENTUAL_TOLERANCIA:
            inconsistencias.append(Inconsistencia(
                cliente=nome, campo="alocacao_total", tipo="soma_invalida",
                descricao=f"Soma dos percentuais = {soma:.1f}% (esperado: 100%).",
                decisao="Dado mantido; inconsistência sinalizada no relatório."
            ))

        # ── Objetivo ─────────────────────────────────────────────────────────
        objetivo = str(row.get("objetivo", "")).strip().lower()
        df.at[idx, "objetivo"] = objetivo
        if objetivo not in OBJETIVOS_VALIDOS:
            inconsistencias.append(Inconsistencia(
                cliente=nome, campo="objetivo", tipo="valor_invalido",
                descricao=f"Objetivo '{objetivo}' não reconhecido. "
                          f"Valores válidos: {OBJETIVOS_VALIDOS}.",
                decisao="Cliente processado; perfil de risco baseado apenas na alocação."
            ))

    logger.info(
        "Validação concluída: %d inconsistência(s) em %d cliente(s).",
        len(inconsistencias), len(df)
    )
    return ResultadoValidacao(df=df, inconsistencias=inconsistencias)
