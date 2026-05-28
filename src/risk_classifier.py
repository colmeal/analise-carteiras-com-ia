"""
risk_classifier.py
Lógica de classificação de perfil de risco e detecção de desalinhamentos.

A classificação usa um sistema de pontuação ponderada que considera:
  - Percentual em ativos de risco (peso maior)
  - Objetivo declarado
  - Idade do cliente
  - Concentração em cripto

Essa abordagem é mais robusta que regras simples if/else porque
trata casos ambíguos de forma gradual e explicável.
"""

from dataclasses import dataclass, field
from utils import get_logger
from config import (
    LIMITE_CONSERVADOR,
    LIMITE_MODERADO,
    CRIPTO_ALERTA_DEFENSIVO,
    CRIPTO_ALERTA_SEVERO,
    IDADE_DESCONHECIDA,
)

logger = get_logger(__name__)


@dataclass
class ResultadoClassificacao:
    """Resultado completo da classificação de risco de um cliente."""
    perfil:        str            # conservador | moderado | arrojado
    score:         float          # pontuação interna (0–100)
    justificativa: str            # explicação legível
    alertas:       list[str] = field(default_factory=list)


def classificar(cliente: dict) -> ResultadoClassificacao:
    """
    Classifica o perfil de risco do cliente usando sistema de pontuação ponderada.

    Score de 0 (ultrar-conservador) a 100 (ultra-arrojado):
      - 0–33   → conservador
      - 34–66  → moderado
      - 67–100 → arrojado

    Args:
        cliente: Dicionário com os campos do cliente já validados

    Returns:
        ResultadoClassificacao com perfil, score, justificativa e alertas
    """
    nome      = cliente.get("nome", "Cliente")
    objetivo  = str(cliente.get("objetivo", "")).lower()
    idade     = int(cliente.get("idade", IDADE_DESCONHECIDA))
    perc_rv   = float(cliente.get("perc_renda_variavel", 0))
    perc_rf   = float(cliente.get("perc_renda_fixa", 0))
    perc_cri  = float(cliente.get("perc_cripto", 0))
    perc_risco = perc_rv + perc_cri

    fatores: list[str] = []
    score = 0.0

    # ── Fator 1: Exposição a ativos de risco (peso 50%) ──────────────────────
    score_risco = min(perc_risco, 100) * 0.50
    score += score_risco
    fatores.append(
        f"{perc_risco:.0f}% em ativos de risco (variável + cripto)"
    )

    # ── Fator 2: Objetivo declarado (peso 30%) ────────────────────────────────
    score_objetivo = 0.0
    if objetivo == "crescimento":
        score_objetivo = 30.0
        fatores.append("objetivo: crescimento (perfil mais arrojado)")
    elif objetivo == "preservacao":
        score_objetivo = 5.0
        fatores.append("objetivo: preservação (perfil defensivo)")
    elif objetivo == "aposentadoria":
        score_objetivo = 8.0
        fatores.append("objetivo: aposentadoria (perfil defensivo)")
    else:
        score_objetivo = 15.0
        fatores.append("objetivo desconhecido (neutro)")
    score += score_objetivo

    # ── Fator 3: Idade (peso 20%) ─────────────────────────────────────────────
    score_idade = 0.0
    if idade == IDADE_DESCONHECIDA:
        score_idade = 10.0
        fatores.append("idade não informada (assumido neutro)")
    elif idade < 35:
        score_idade = 20.0
        fatores.append(f"idade {idade} anos (jovem — maior tolerância ao risco)")
    elif idade < 50:
        score_idade = 12.0
        fatores.append(f"idade {idade} anos (maturidade média)")
    elif idade < 65:
        score_idade = 6.0
        fatores.append(f"idade {idade} anos (próximo à aposentadoria)")
    else:
        score_idade = 2.0
        fatores.append(f"idade {idade} anos (fase de preservação recomendada)")
    score += score_idade

    # ── Determinar perfil pelo score ──────────────────────────────────────────
    if score <= 33:
        perfil = "conservador"
    elif score <= 66:
        perfil = "moderado"
    else:
        perfil = "arrojado"

    justificativa = (
        f"Score de risco: {score:.1f}/100. Fatores considerados: "
        + "; ".join(fatores) + "."
    )

    # ── Detecção de alertas de desalinhamento ─────────────────────────────────
    alertas: list[str] = []

    if objetivo in ("aposentadoria", "preservacao") and perc_risco > 30:
        alertas.append(
            f"Alocação de risco ({perc_risco:.0f}%) elevada para objetivo '{objetivo}'. "
            "Recomenda-se revisão da carteira."
        )

    if objetivo in ("aposentadoria", "preservacao") and perc_cri > CRIPTO_ALERTA_DEFENSIVO:
        alertas.append(
            f"{perc_cri:.0f}% em cripto é excessivo para objetivo '{objetivo}'. "
            "Criptoativos apresentam volatilidade incompatível com perfis defensivos."
        )

    if perc_cri >= CRIPTO_ALERTA_SEVERO:
        alertas.append(
            f"ALERTA SEVERO: {perc_cri:.0f}% do patrimônio em cripto. "
            "Risco de concentração extremo — exposição muito acima do aceitável."
        )

    if perc_rf > 90 and objetivo == "crescimento":
        alertas.append(
            f"{perc_rf:.0f}% em renda fixa para objetivo 'crescimento'. "
            "Carteira possivelmente subotimizada para o objetivo declarado."
        )

    if idade != IDADE_DESCONHECIDA and idade > 65 and perc_risco > 40:
        alertas.append(
            f"Cliente com {idade} anos e {perc_risco:.0f}% em risco — "
            "exposição elevada para a faixa etária."
        )

    if alertas:
        logger.warning("%s — %d alerta(s) de desalinhamento.", nome, len(alertas))

    return ResultadoClassificacao(
        perfil=perfil,
        score=round(score, 1),
        justificativa=justificativa,
        alertas=alertas,
    )
