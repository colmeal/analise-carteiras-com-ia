"""
data_loader.py
Responsável exclusivamente pela leitura da planilha Excel.
Não faz validação — essa responsabilidade pertence ao validator.py.
"""

from pathlib import Path
import pandas as pd
from utils import get_logger
from config import COLUNAS_OBRIGATORIAS

logger = get_logger(__name__)


def carregar_planilha(caminho: Path) -> pd.DataFrame:
    """
    Lê o arquivo Excel e retorna o DataFrame bruto.

    Args:
        caminho: Caminho para o arquivo .xlsx

    Returns:
        DataFrame com os dados brutos da planilha

    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se colunas obrigatórias estiverem ausentes
        RuntimeError: Para outros erros de leitura
    """
    if not caminho.exists():
        raise FileNotFoundError(
            f"Planilha não encontrada: {caminho}\n"
            f"Coloque o arquivo na pasta 'data/' antes de rodar o projeto."
        )

    try:
        df = pd.read_excel(caminho, engine="openpyxl")
        logger.info("Planilha carregada: %d registros, %d colunas.", len(df), len(df.columns))
    except Exception as exc:
        raise RuntimeError(f"Erro ao ler a planilha: {exc}") from exc

    # Normaliza nomes de colunas: remove espaços e converte para minúsculo
    df.columns = [c.strip().lower() for c in df.columns]

    colunas_ausentes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if colunas_ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes na planilha: {colunas_ausentes}\n"
            f"Colunas encontradas: {list(df.columns)}"
        )

    return df
