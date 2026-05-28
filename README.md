# # Análise de Carteiras com IA

Sistema de análise automatizada de carteiras de clientes utilizando Python, pandas e IA generativa (Gemini). Projeto desenvolvido para simular um pipeline automatizado de análise de carteiras financeiras com apoio de IA generativa.

---

## Visão geral

O sistema processa uma planilha com dados de clientes, valida e trata inconsistências, classifica automaticamente o perfil de risco de cada cliente com base em um sistema de pontuação ponderada, e utiliza IA para gerar análises financeiras em linguagem natural. O resultado é entregue em dois formatos: JSON estruturado e TXT legível.

---

## Arquitetura

```
tag_desafio/
│
├── data/                        # Arquivos de entrada (não versionados)
│   └── clientes_carteira.xlsx
│
├── output/                      # Relatórios gerados (não versionados)
│   ├── relatorio.json
│   └── relatorio.txt
│
├── src/
│   ├── main.py                  # Orquestrador — pipeline completo
│   ├── config.py                # Configurações e constantes centralizadas
│   ├── data_loader.py           # Leitura e verificação da planilha
│   ├── validator.py             # Validação e normalização dos dados
│   ├── risk_classifier.py       # Classificação de risco por score ponderado
│   ├── ai_analyzer.py           # Integração com API Gemini
│   ├── report_generator.py      # Geração dos relatórios JSON e TXT
│   └── utils.py                 # Logging e funções utilitárias
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

**Responsabilidade de cada módulo:**

| Arquivo | Responsabilidade |
|---|---|
| `config.py` | Único ponto de acesso a variáveis de ambiente, constantes e thresholds |
| `data_loader.py` | Leitura do arquivo Excel, normalização de colunas |
| `validator.py` | Detecção e tratamento de inconsistências com registro de decisões |
| `risk_classifier.py` | Score ponderado de risco + detecção de desalinhamentos |
| `ai_analyzer.py` | Prompt engineering, chamada à API, retry com backoff exponencial |
| `report_generator.py` | Serialização para JSON e formatação do relatório TXT |
| `utils.py` | Logger configurado, formatadores de moeda e percentual |

---

## Tecnologias

- **Python 3.11+**
- **pandas** — leitura e manipulação da planilha
- **openpyxl** — engine para arquivos `.xlsx`
- **google-generativeai** — API Gemini (gemini-1.5-flash)
- **python-dotenv** — carregamento seguro de variáveis de ambiente
- **logging** — logs estruturados com timestamp e nível

---

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd tag_desafio

# 2. Crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure a chave de API
cp .env.example .env
# Edite o .env e insira sua GEMINI_API_KEY
```

---

## Variáveis de ambiente

| Variável | Descrição | Obrigatória |
|---|---|---|
| `GEMINI_API_KEY` | Chave de API do Google AI Studio | Sim |

Obtenha uma chave gratuita em: [aistudio.google.com](https://aistudio.google.com/app/apikey)

---

## Execução

```bash
# Coloque a planilha em data/clientes_TAG.xlsx
# Depois, dentro da pasta src/:

cd src
python main.py
```

Os relatórios serão gerados em `output/relatorio.json` e `output/relatorio.txt`.

---

## Tratamento de inconsistências

A planilha foi criada com dados propositalmente inconsistentes. Cada caso é tratado de forma explícita, registrado no relatório e documentado com a decisão tomada:

| Cliente | Inconsistência | Decisão |
|---|---|---|
| Isabela Prado | `perc_cripto` nulo + soma ≠ 100% | Cripto assumida como 0%; inconsistência registrada |
| Thiago Azevedo | `patrimonio_total` nulo | Assumido como R$ 0; informado na análise de IA |
| Eduardo Fontes | `idade` nula | Substituída por sentinela -1; classificação com ressalva |
| Fernanda Queiroz | 80% em cripto + objetivo preservação | Alerta severo gerado; IA instruda do desalinhamento |
| Sônia Brandão | 75% variável + 69 anos + aposentadoria | Alerta de exposição elevada para a faixa etária |

---

## Decisões técnicas

**Classificação por score ponderado (não if/else simples)**
Em vez de uma cascata de condicionais, o perfil de risco é derivado de um score de 0 a 100 calculado com três fatores: exposição a risco (50%), objetivo (30%) e idade (20%). Isso permite tratar casos ambíguos de forma gradual e explicável, e facilita ajuste dos pesos sem reescrever a lógica.

**Separação validator.py / data_loader.py**
Leitura e validação têm responsabilidades distintas. O `data_loader` só sabe ler arquivos; o `validator` só sabe validar dados. Isso segue o Princípio da Responsabilidade Única e facilita testes isolados.

**config.py como fonte única de verdade**
Todos os thresholds (limites de risco, tolerâncias, nomes de arquivo) estão em `config.py`. Alterar o limite de cripto para alertas, por exemplo, requer uma mudança em um único lugar.

**Retry com backoff exponencial na API**
Chamadas de API falham por razões temporárias (rate limit, timeout de rede). O backoff exponencial (1s, 2s, 4s) respeita os limites da API sem sobrecarregá-la, e o fluxo continua para os demais clientes mesmo se um falhar.

**Dois formatos de saída**
O JSON é consumível por outros sistemas (dashboards, planilhas, APIs). O TXT é legível por qualquer pessoa sem ferramentas adicionais — relevante em um contexto corporativo onde nem todos têm acesso a ferramentas técnicas.

---

## Melhorias futuras

| Melhoria | Valor para estágio | Observação |
|---|---|---|
| Envio por e-mail (smtplib) | Alto | Demonstra integração ponta-a-ponta |
| Exportação para Google Sheets | Alto | Encaixa no workflow corporativo |
| Testes unitários (pytest) | Alto | Diferencial técnico relevante |
| Cache de respostas da IA | Médio | Reduz custo em reprocessamentos |
| Docker | Baixo | Útil, mas excessivo para estágio |
| CI/CD | Baixo | Fora do escopo de estágio |

---

## Segurança

- Chave de API carregada exclusivamente via `.env` + `python-dotenv`
- Arquivo `.env` no `.gitignore` — nunca versionado
- Dados de clientes (`data/`) e relatórios (`output/`) no `.gitignore`
- Nenhuma informação sensível em logs ou comentários

---

## Exemplo de saída (JSON)

```json
{
  "nome": "Fernanda Queiroz",
  "perfil_risco": "arrojado",
  "score_risco": 72.0,
  "alertas": [
    "80% em cripto é excessivo para objetivo 'preservacao'.",
    "ALERTA SEVERO: 80% do patrimônio em cripto."
  ],
  "status": "ALERTA",
  "resumo_ia": "A carteira de Fernanda apresenta concentração extrema..."
}
```

---

## Uso de IA no desenvolvimento

Este projeto foi desenvolvido com auxílio de IA (Claude). Todo código foi revisado, compreendido e adaptado ao contexto do desafio. Cada decisão de arquitetura e implementação pode ser explicada e justificada.
