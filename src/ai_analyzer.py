"""
ai_analyzer.py
Integração com a API Gemini para análise financeira em linguagem natural.
"""

import time
from google import genai
from google.genai import types
from utils import get_logger
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    API_MAX_RETRIES,
    API_RETRY_DELAY,
    IDADE_DESCONHECIDA,
)

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Você é um analista sênior de gestão de patrimônio da TAG Investimentos, "
    "especializado em análise de risco e alocação de carteiras para famílias de alta renda, "
    "fundações e seguradoras. Suas análises são diretas, técnicas e orientadas a ação."
)


def configurar_cliente() -> genai.Client:
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY não definida. "
            "Crie o arquivo .env com: GEMINI_API_KEY=sua_chave"
        )

    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("Cliente Gemini configurado. Modelo: %s", GEMINI_MODEL)
    return client


def _montar_prompt(
    cliente: dict,
    perfil: str,
    score: float,
    alertas: list[str],
    justificativa: str,
) -> str:
    idade_str = (
        str(int(cliente["idade"]))
        if int(cliente["idade"]) != IDADE_DESCONHECIDA
        else "não informada"
    )

    patrimonio_str = (
        f"R$ {float(cliente['patrimonio_total']):,.0f}"
        if float(cliente["patrimonio_total"]) > 0
        else "não informado"
    )

    alertas_str = (
        "\n".join(f"- {a}" for a in alertas)
        if alertas
        else "- Nenhum desalinhamento crítico identificado."
    )

    return f"""Analise o cliente abaixo para um relatório de gestão de patrimônio.

DADOS DO CLIENTE:
Nome: {cliente['nome']}
Idade: {idade_str}
Patrimônio: {patrimonio_str}
Objetivo: {cliente['objetivo']}
Alocação: {cliente['perc_renda_variavel']}% renda variável, {cliente['perc_renda_fixa']}% renda fixa, {cliente['perc_cripto']}% cripto.

CLASSIFICAÇÃO INTERNA:
Perfil de risco: {perfil}
Score de risco: {score}/100
Justificativa: {justificativa}

ALERTAS:
{alertas_str}

TAREFA:
Escreva exatamente 1 parágrafo completo, entre 500 e 700 caracteres.
O parágrafo deve incluir:
1. se a carteira está consistente ou não com o objetivo declarado;
2. o principal risco identificado;
3. uma recomendação objetiva.
Não use markdown. Não use listas. Não use título. Não termine no meio da frase.
Responda em português brasileiro."""


def _extrair_texto_resposta(resposta) -> str:
    """
    Extrai o texto da resposta do Gemini de forma mais segura.
    Em alguns casos, resposta.text pode vir vazio/incompleto dependendo do SDK.
    """
    if getattr(resposta, "text", None):
        return resposta.text.strip()

    partes_texto = []

    candidates = getattr(resposta, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content else None

        if parts:
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    partes_texto.append(text)

    return "\n".join(partes_texto).strip()


def analisar_com_ia(
    model: genai.Client,
    cliente: dict,
    perfil: str,
    score: float,
    alertas: list[str],
    justificativa: str,
) -> str:
    prompt = _montar_prompt(cliente, perfil, score, alertas, justificativa)
    nome = cliente.get("nome", "Cliente")

    for tentativa in range(1, API_MAX_RETRIES + 1):
        try:
            logger.debug("Chamando API para '%s' (tentativa %d).", nome, tentativa)

            resposta = model.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=2048,
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )

            texto = _extrair_texto_resposta(resposta)

            if not texto:
                raise ValueError("Resposta vazia da IA.")

            if len(texto) < 120:
                logger.warning(
                    "Resposta curta da IA para '%s'. Mantendo texto retornado.",
                    nome,
                )

            time.sleep(2.0)
            return texto

        except Exception as exc:
            logger.warning(
                "Tentativa %d/%d falhou para '%s': %s",
                tentativa,
                API_MAX_RETRIES,
                nome,
                exc,
            )

            if tentativa < API_MAX_RETRIES:
                espera = max(API_RETRY_DELAY, 5.0) * (2 ** (tentativa - 1))
                logger.info("Aguardando %.1fs antes de nova tentativa...", espera)
                time.sleep(espera)

    logger.error("Todas as tentativas falharam para '%s'.", nome)
    return (
        "[Análise indisponível] Não foi possível obter resposta completa da API após "
        f"{API_MAX_RETRIES} tentativas."
    )