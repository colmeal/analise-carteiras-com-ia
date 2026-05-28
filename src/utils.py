"""
utils.py
Utilitários compartilhados: configuração de logging, formatação e helpers gerais.
"""

import logging
from config import LOG_LEVEL, LOG_FORMAT, LOG_DATE


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado com o padrão do projeto.
    Cada módulo chama get_logger(__name__) para rastreabilidade nos logs.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
        logger.addHandler(handler)

    logger.setLevel(LOG_LEVEL)
    return logger


def formatar_moeda(valor: float) -> str:
    """Formata um valor numérico como moeda brasileira. Ex: 1500000 → 'R$ 1.500.000,00'"""
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ —"


def formatar_percentual(valor: float) -> str:
    """Formata um valor como percentual. Ex: 45.5 → '45.5%'"""
    try:
        return f"{float(valor):.1f}%"
    except (TypeError, ValueError):
        return "—%"
