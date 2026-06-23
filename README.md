<div align="center">
  <img src="https://raw.githubusercontent.com/confident-ai/deepeval/main/docs/static/img/logo.svg" alt="DeepEval Logo" width="120" height="120">
  <h1>🛡️ AWS LLMOps Quality Gates</h1>
  <p><strong>Barreira de Qualidade Automatizada para Pipelines RAG (Retrieval-Augmented Generation)</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
  [![DeepEval](https://img.shields.io/badge/DeepEval-4.0%2B-6200FF.svg)](https://docs.confident-ai.com/)
  [![Pytest](https://img.shields.io/badge/Pytest-8.0%2B-0A9EDC.svg)](https://docs.pytest.org/)
  [![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-FF9900.svg)](https://aws.amazon.com/bedrock/)
  [![CI/CD](https://img.shields.io/badge/GitHub_Actions-Passing-success.svg)](https://github.com/features/actions)
</div>

<br>

> Uma suíte programática de testes unitários que implementa uma arquitetura **LLM-as-a-Judge** utilizando Amazon Bedrock (Claude) para atuar como um **Quality Gate** estrito. Esta esteira previne regressões de qualidade, forçando *build breaks* automatizados caso detecte alucinações, evasões, injeções de prompt ou falhas de recuperação semântica antes que os artefatos alcancem o ambiente de produção.

---

## 📑 Índice

- [✨ Principais Recursos](#-principais-recursos)
- [📐 Arquitetura da Solução](#-arquitetura-da-solução)
- [🗺️ Matriz de Cobertura de Testes](#-matriz-de-cobertura-de-testes)
- [📦 Estrutura do Repositório](#-estrutura-do-repositório)
- [🚀 Guia de Instalação Rápida](#-guia-de-instalação-rápida)
- [🔄 Integração CI/CD](#-integração-cicd)
- [🔬 Engenharia de Testes TDD e Cenários](#-engenharia-de-testes-tdd-e-cenários)
- [🛠️ Guia de Extensibilidade](#️-guia-de-extensibilidade)
- [🚨 Troubleshooting](#-troubleshooting)
- [📚 Próximos Passos](#-próximos-passos)

---

## ✨ Principais Recursos

- **Validação em Nível de Produção:** Abandone os `vibe checks`. Execute avaliações determinísticas em CI/CD baseadas na "Tríade do RAG" (*Contextual Precision*, *Faithfulness* e *Answer Relevancy*).
- **Amazon Bedrock Integrado:** Utiliza LLMs *state-of-the-art* da AWS (como o Anthropic Claude 3.5 Sonnet) como juízes implacáveis, mantendo a privacidade e segurança dos dados sob a governança da sua conta AWS.
- **15 Cenários Comportamentais RAG Simulados:** Desde *happy paths* até casos de borda (*edge cases*) avançados (como *Semantic Drift*, *Entity Swaps* e *Prompt Injection*), simulando falhas reais e ataques que podem ocorrer.
- **Integração Nativa com Pytest:** A suíte suporta recursos nativos do ecossistema `pytest` (marcadores personalizados, execução paralela e geração de relatórios de falhas extraídos programaticamente).
- **Segurança e Alinhamento (Safety Gates):** Filtros que vetam imediatamente comportamentos inadequados, como toxicidade, viés cognitivo/comportamental, e injeção de prompt.

---

## 📐 Arquitetura da Solução

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffffff', 'primaryBorderColor': '#333333', 'primaryTextColor': '#333333', 'lineColor': '#6200FF'}}}%%
flowchart TB
    subgraph CI["Pipeline CI/CD (GitHub Actions)"]
        direction TB
        PUSH["🔀 Pull Request"]
        LINT["🔍 Análise Estática (Ruff/MyPy)"]
        GATE["🛡️ Quality Gate (DeepEval)"]
        DECISION{"🚦 Decisão"}
        DEPLOY["🚀 Merge / Deploy"]
        BLOCK["🚨 Build Break"]
        
        PUSH --> LINT --> GATE --> DECISION
        DECISION -- "✅ 19/19 Pass" --> DEPLOY
        DECISION -- "❌ Falha detectada" --> BLOCK
    end

    subgraph QG["Motor de Avaliação (Quality Gate)"]
        direction TB
        MOCK["📦 SageMaker Mock Pipeline\n(15 Edge Cases)"]
        TESTS["🧪 Pytest Assertions\n(Tríade RAG + Safety)"]
        JUDGE["⚖️ Amazon Bedrock\n(Claude 3.5 Sonnet)"]
        
        MOCK -->|Context & Output| TESTS
        TESTS -->|Prompt Evaluation| JUDGE
        JUDGE -->|Score & Reason| TESTS
    end

    GATE --> QG
```

---

## 🗺️ Matriz de Cobertura de Testes

Foram implementados testes estritos (asserções), projetados para garantir os pilares da qualidade generativa.

> [!IMPORTANT]
> **Thresholds (Limiares)**: Os limites estão configurados de forma agressiva (0.85 — 0.90) para o padrão *enterprise*. Ajuste-os caso a taxa de falsos positivos bloqueie excessivamente a esteira em fases iniciais de desenvolvimento.

### 📌 Tríade do RAG
| Categoria | ID | Métrica (DeepEval) | 🎯 Objetivo | Limiar |
|-----------|----|--------------------|-------------|:---:|
| **Faithfulness** | `FAITH-01` a `05` | `FaithfulnessMetric` | Valida ancoragem factual. Pune fatos alucinados, troca de entidades, injeções e falas fora de domínio. | `>= 0.85` |
| **Answer Relevance** | `RELEV-01` a `04` | `AnswerRelevancyMetric` | Penaliza respostas evasivas, genéricas, fora de tópico e que quebrem regras estritas de formatação. | `>= 0.85` |
| **Context Precision**| `PREC-01` a `03` | `ContextualPrecisionMetric` | Avalia o ranqueamento dos documentos no *Vector Database*. A presença de ruído dilui a pontuação. | `>= 0.85` |

### 📌 Métricas Complementares e de Segurança
| Categoria | ID | Métrica (DeepEval) | 🎯 Objetivo | Limiar |
|-----------|----|--------------------|-------------|:---:|
| **Context Recall** | `RECALL-01` a `02` | `ContextualRecallMetric` | O recuperador trouxe toda a base necessária? Detecta gaps informacionais. | `>= 0.85` |
| **Safety / Toxicidade** | `SAFE-01` a `03` | `ToxicityMetric` e `HallucinationMetric` | Bloqueia saídas com linguagem ofensiva, tóxica ou alucinada. | `>= 0.85` |
| **Safety / Viés** | `SAFE-04` | `BiasMetric` | Análise para evitar viés difamatório ou corporativo não justificado. | `>= 0.85` |
| **Context Relevancy**| `CTX-REL-01` | `ContextualRelevancyMetric` | Densidade informacional. Penaliza chunks desnecessariamente massivos. | `>= 0.85` |

---

## 📦 Estrutura do Repositório

```text
aws-llmops-quality-gates/
├── .github/workflows/
│   └── rag-quality-gate.yml    # Pipeline GitHub Actions com suporte a OIDC e Bedrock
├── src/
│   └── rag_pipeline_mock.py    # Wrapper simulando respostas e falhas do SageMaker (15 cenários)
├── tests/
│   ├── conftest.py             # Fixtures Pytest, inicialização do Amazon Bedrock e logs
│   └── test_rag_quality.py     # Asserções de Qualidade
├── pytest.ini                  # Configurações de marcadores e caminhos
├── requirements.txt            # Dependências
└── README.md                   # Documentação do projeto
```

---

## 🚀 Guia de Instalação Rápida

### 1. Pré-requisitos do Ambiente

- **Python**: Versão `3.9` ou superior.
- **AWS Account**: Acesso programático configurado.
- **Model Access**: Verifique se a sua conta possui acesso habilitado aos modelos no [Amazon Bedrock Console](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html).

### 2. Instalação Básica

```bash
# Clone o repositório e crie o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Ou .venv\Scripts\activate no Windows

# Instale as dependências do projeto
pip install -r requirements.txt
```

### 3. Autenticação AWS

Os testes utilizam o SDK `boto3` para realizar as chamadas ao Amazon Bedrock. Configure suas credenciais da AWS utilizando uma das abordagens a seguir:

**No Linux/macOS (Bash):**
```bash
aws configure sso --profile seu-perfil-sso
export AWS_PROFILE=seu-perfil-sso
```

**No Windows (PowerShell):**
```powershell
aws configure sso --profile seu-perfil-sso
$env:AWS_PROFILE="seu-perfil-sso"
```

### 4. Executando o Quality Gate

```bash
# Executa todos os testes e exibe os motivos (.reason) no final
deepeval test run tests/test_rag_quality.py -v

# Ou utilize filtros por tags (marcadores definidos no pytest.ini)
pytest tests/test_rag_quality.py -m "faithfulness" -v
pytest tests/test_rag_quality.py -m "safety" -v
```

> [!TIP]
> Por padrão, o framework utiliza o modelo `anthropic.claude-3-5-sonnet-20241022-v2:0`. Para alterar o modelo juiz, configure a variável de ambiente `BEDROCK_MODEL_ID`.

---

## 🔄 Integração CI/CD

O repositório inclui um arquivo `.github/workflows/rag-quality-gate.yml`. Configure a `AWS_ROLE_ARN` nos segredos do GitHub para autenticação OIDC segura. Sempre que a pipeline falha em um Pull Request, um comentário com o `metric.reason` é gerado para facilitar o debugging.

---

## 🔬 Engenharia de Testes TDD e Cenários

Para garantir que o Quality Gate não é frágil, construímos um arquivo `src/rag_pipeline_mock.py` que emula **15 cenários** (positivos e negativos) de um RAG em produção.

**Exemplos de Cenários Críticos e Avançados:**
- `hallucinated_response`: Resposta com fatos inventados (testa *Faithfulness*).
- `semantic_drift`: O LLM inicia a resposta correta, mas "deriva" para tópicos irrelevantes.
- `contradictory_context`: Simulamos a entrega de dois chunks conflitantes pelo Retriever.
- `prompt_injection` *(Novo)*: Tentativa de sobrepor as instruções de sistema, forçando o modelo a agir como outro persona.
- `toxic_output` e `biased_output` *(Novos)*: Simula respostas ofensivas ou enviesadas, atestando a eficácia dos testes de segurança.
- `formatting_failure` *(Novo)*: O LLM ignora o formato JSON e retorna markdown, provando a detecção de quebra de contrato (esquema).

---

## 🛠️ Guia de Extensibilidade

Para adicionar novos cenários e métricas:
1. Adicione o novo `RAGTestScenario` em `src/rag_pipeline_mock.py`.
2. Adicione a `fixture` respectiva no `tests/conftest.py`.
3. Escreva um novo `test_` em `tests/test_rag_quality.py` utilizando a métrica correspondente do DeepEval.
4. Execute e valide se a pipeline quebra de acordo com a sua expectativa.

---

## 🚨 Troubleshooting

- **`AccessDeniedException`**: Ocorre quando o IAM/SSO atual não tem permissão de usar a API `bedrock:InvokeModel`. Verifique seu AWS Profile ou habilite o acesso ao modelo na console do Bedrock.
- **`ReadTimeoutError` ou Demora Extrema**: A inferência do modelo juiz pode demorar caso os limites de RPM (Requests Per Minute) tenham sido atingidos ou se a conexão cair. O DeepEval tentará retries.
- **`ModelNotReadyException`**: O modelo selecionado (ex: um Claude novo) pode não estar disponível na região configurada. Mude `BEDROCK_REGION` para `us-east-1` ou `us-west-2`.

---

## 📚 Próximos Passos

Esta arquitetura serve como base. Conforme a aplicação RAG escalar, recomenda-se:
1. **Avaliações em Lote Diárias:** Agendar o Workflow (CRON) para avaliar o modelo recém-treinado no S3 contra um "Golden Dataset" de centenas de perguntas.
2. **Observabilidade (Confident AI / Phoenix):** Exportar os traces e scores do Bedrock para uma interface de Telemetria centralizada.
3. **Métricas de Agentic Frameworks**: Introduzir testes focados em chamadas de ferramenta (*Tool Use*) e *Agent Reasoning*.
