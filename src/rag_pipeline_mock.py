"""
RAG Pipeline Mock — Simulação do endpoint AWS SageMaker.

Este módulo implementa um wrapper simulado que replica a interface de um
pipeline RAG servido via AWS SageMaker, retornando as três variáveis
exigidas para avaliação profunda pelo DeepEval:

    - input:             A pergunta do usuário
    - actual_output:     A resposta gerada pelo modelo
    - retrieval_context: A lista de chunks recuperados do vector store
    - expected_output:   Ground truth para métricas de recall (quando aplicável)

Os cenários são divididos em duas categorias:
    CRÍTICOS (1-5):  Cobrem os vetores fundamentais de falha de um RAG.
    AVANÇADOS (6-10): Cobrem edge cases de produção e falhas silenciosas.

Autor: MLOps Quality Gate Pipeline
Compatível com: deepeval >= 4.0 | pytest >= 8.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class RAGTestScenario:
    """Representa um cenário de teste para o pipeline RAG.

    Attributes:
        scenario_id: Identificador único do cenário.
        scenario_name: Nome descritivo para logging.
        description: Descrição do comportamento esperado.
        input: A pergunta do usuário.
        actual_output: A resposta gerada pelo modelo (LLM).
        retrieval_context: Lista de chunks recuperados pelo retriever.
        expected_output: Ground truth para métricas de recall.
        context: Lista de contextos factuais para HallucinationMetric.
    """

    scenario_id: str
    scenario_name: str
    description: str
    input: str
    actual_output: str
    retrieval_context: list[str]
    expected_output: Optional[str] = None
    context: list[str] = field(default_factory=list)


class RAGPipelineMock:
    """Wrapper simulado do pipeline RAG servido via AWS SageMaker.

    Simula a chamada ao endpoint SageMaker e retorna cenários pré-definidos
    que exercitam diferentes vetores de falha de qualidade em pipelines RAG.

    Usage:
        >>> pipeline = RAGPipelineMock()
        >>> scenario = pipeline.get_scenario("happy_path")
        >>> print(scenario.input, scenario.actual_output)
    """

    def __init__(self) -> None:
        """Inicializa o mock com todos os cenários registrados."""
        self._scenarios: dict[str, RAGTestScenario] = {}
        self._register_critical_scenarios()
        self._register_advanced_scenarios()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def get_scenario(self, scenario_id: str) -> RAGTestScenario:
        """Retorna um cenário de teste pelo ID.

        Args:
            scenario_id: Identificador do cenário.

        Returns:
            RAGTestScenario correspondente.

        Raises:
            KeyError: Se o cenário não existir.
        """
        if scenario_id not in self._scenarios:
            available = ", ".join(sorted(self._scenarios.keys()))
            raise KeyError(
                f"Cenário '{scenario_id}' não encontrado. "
                f"Disponíveis: {available}"
            )
        return self._scenarios[scenario_id]

    def list_scenarios(self) -> list[str]:
        """Retorna todos os IDs de cenários disponíveis."""
        return sorted(self._scenarios.keys())

    # =========================================================================
    # CENÁRIOS CRÍTICOS (1-5)
    # =========================================================================

    def _register_critical_scenarios(self) -> None:
        """Registra os 5 cenários críticos de teste."""

        # -----------------------------------------------------------------
        # CENÁRIO 1: Happy Path — Resposta perfeita, alinhada ao contexto
        # -----------------------------------------------------------------
        self._scenarios["happy_path"] = RAGTestScenario(
            scenario_id="happy_path",
            scenario_name="Happy Path — Resposta Fidedigna",
            description=(
                "O modelo gera uma resposta estritamente baseada nos chunks "
                "recuperados, sem adicionar informação externa. Todos os "
                "chunks são altamente relevantes e o ranking está correto."
            ),
            input=(
                "Quais são os principais benefícios do Amazon SageMaker "
                "para treinamento distribuído de modelos de Machine Learning?"
            ),
            actual_output=(
                "Os principais benefícios do Amazon SageMaker para "
                "treinamento distribuído incluem: (1) escalabilidade "
                "automática de instâncias de treinamento com suporte a "
                "GPU e clusters multi-nó, (2) integração nativa com o "
                "Amazon S3 para armazenamento de datasets e artefatos "
                "de modelo, e (3) bibliotecas otimizadas como a SageMaker "
                "Distributed Training Library que paraleliza automaticamente "
                "os workloads entre múltiplas instâncias."
            ),
            retrieval_context=[
                (
                    "O Amazon SageMaker oferece escalabilidade automática "
                    "para instâncias de treinamento, incluindo suporte a GPU "
                    "e clusters multi-nó para treinamento distribuído de "
                    "modelos de Machine Learning de grande escala."
                ),
                (
                    "O SageMaker possui integração nativa com o Amazon S3, "
                    "permitindo o armazenamento eficiente de datasets de "
                    "treinamento e artefatos de modelo, simplificando o "
                    "gerenciamento de dados durante o ciclo de vida do ML."
                ),
                (
                    "A SageMaker Distributed Training Library é uma "
                    "biblioteca otimizada que paraleliza automaticamente "
                    "os workloads de treinamento entre múltiplas instâncias, "
                    "suportando tanto data parallelism quanto model "
                    "parallelism para modelos de grande escala."
                ),
            ],
            expected_output=(
                "Os benefícios do SageMaker para treinamento distribuído "
                "são: escalabilidade automática com GPU e clusters multi-nó, "
                "integração nativa com S3 para dados e artefatos, e a "
                "SageMaker Distributed Training Library para paralelização "
                "automática dos workloads."
            ),
            context=[
                (
                    "O Amazon SageMaker oferece escalabilidade automática "
                    "para instâncias de treinamento, incluindo suporte a GPU "
                    "e clusters multi-nó."
                ),
                (
                    "O SageMaker possui integração nativa com o Amazon S3 "
                    "para armazenamento de datasets e artefatos de modelo."
                ),
                (
                    "A SageMaker Distributed Training Library paraleliza "
                    "automaticamente os workloads de treinamento entre "
                    "múltiplas instâncias."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 2: Alucinação — Resposta com fatos fabricados
        # -----------------------------------------------------------------
        self._scenarios["hallucinated_response"] = RAGTestScenario(
            scenario_id="hallucinated_response",
            scenario_name="Alucinação — Fatos Fabricados",
            description=(
                "O modelo gera uma resposta que contém informações "
                "completamente inventadas, não presentes no contexto "
                "recuperado. Simula a principal falha silenciosa em RAG."
            ),
            input=(
                "Qual é a política de preços do Amazon Bedrock para "
                "modelos foundation?"
            ),
            actual_output=(
                "O Amazon Bedrock oferece preços pay-per-use baseados "
                "em tokens processados. Além disso, o Bedrock oferece "
                "um plano gratuito permanente de 1 milhão de tokens por "
                "mês para todos os modelos foundation, e um desconto de "
                "90% para clientes que migram do Azure OpenAI Service. "
                "A AWS também garante que nenhum modelo no Bedrock "
                "custará mais que USD 0.001 por token até 2030."
            ),
            retrieval_context=[
                (
                    "O Amazon Bedrock utiliza precificação pay-per-use, "
                    "onde os clientes pagam com base no número de tokens "
                    "de entrada e saída processados durante as chamadas "
                    "de API para os modelos foundation."
                ),
                (
                    "O Bedrock suporta modelos de provedores como "
                    "Anthropic, Meta, Mistral e Amazon, cada um com "
                    "tabelas de preços específicas por modelo e região."
                ),
            ],
            expected_output=(
                "O Amazon Bedrock usa preços pay-per-use por tokens "
                "processados, com tabelas específicas por modelo e região."
            ),
            context=[
                (
                    "O Amazon Bedrock utiliza precificação pay-per-use "
                    "baseada em tokens processados."
                ),
                (
                    "Cada modelo foundation no Bedrock possui tabelas "
                    "de preços específicas por modelo e região."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 3: Resposta Evasiva — Não endereça a pergunta
        # -----------------------------------------------------------------
        self._scenarios["evasive_response"] = RAGTestScenario(
            scenario_id="evasive_response",
            scenario_name="Resposta Evasiva — Falta de Diretividade",
            description=(
                "O modelo retorna uma resposta genérica e tangencial "
                "que não responde diretamente à pergunta do usuário. "
                "Simula o comportamento de modelos sobre-cautelosos."
            ),
            input=(
                "Qual o limite máximo de tamanho de payload para "
                "invocação síncrona de um endpoint SageMaker real-time?"
            ),
            actual_output=(
                "O Amazon SageMaker é um serviço gerenciado de Machine "
                "Learning que facilita a construção, treinamento e "
                "deployment de modelos. Ele oferece diversas opções de "
                "inferência, incluindo endpoints real-time, serverless "
                "e batch transform. Para informações detalhadas sobre "
                "limites e quotas, recomendamos consultar a documentação "
                "oficial da AWS."
            ),
            retrieval_context=[
                (
                    "O limite máximo de tamanho de payload para invocação "
                    "síncrona de um endpoint SageMaker real-time é de 6 MB. "
                    "Para payloads maiores, recomenda-se utilizar a "
                    "invocação assíncrona, que suporta até 1 GB."
                ),
                (
                    "Os endpoints SageMaker real-time possuem um timeout "
                    "padrão de 60 segundos para invocações síncronas, "
                    "configurável até o máximo de 3600 segundos."
                ),
            ],
            expected_output=(
                "O limite máximo de payload para invocação síncrona de um "
                "endpoint SageMaker real-time é de 6 MB."
            ),
            context=[
                (
                    "O limite máximo de payload para invocação síncrona é "
                    "de 6 MB."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 4: Contexto Ruidoso — Chunks irrelevantes no ranking
        # -----------------------------------------------------------------
        self._scenarios["noisy_context"] = RAGTestScenario(
            scenario_id="noisy_context",
            scenario_name="Contexto Ruidoso — Chunks Irrelevantes",
            description=(
                "O retriever retorna chunks onde a maioria é irrelevante "
                "para a pergunta. Apenas um chunk contém a informação "
                "necessária, diluído entre ruído informacional."
            ),
            input=(
                "Como configurar autoscaling para endpoints SageMaker?"
            ),
            actual_output=(
                "Para configurar autoscaling em endpoints SageMaker, "
                "você deve registrar o endpoint como um recurso escalável "
                "no Application Auto Scaling, definir uma política de "
                "scaling baseada na métrica InvocationsPerInstance do "
                "CloudWatch, e configurar os limites mínimo e máximo "
                "de instâncias desejados."
            ),
            retrieval_context=[
                (
                    "O Amazon EC2 Auto Scaling permite ajustar "
                    "automaticamente a capacidade de instâncias EC2 em "
                    "resposta a mudanças na demanda. Ele suporta scaling "
                    "policies baseadas em métricas do CloudWatch."
                ),
                (
                    "O AWS Lambda é um serviço serverless que executa "
                    "código em resposta a eventos. Ele escala "
                    "automaticamente sem necessidade de configuração "
                    "de infraestrutura."
                ),
                (
                    "Para configurar autoscaling em endpoints SageMaker, "
                    "registre o endpoint como recurso escalável no "
                    "Application Auto Scaling. Defina uma política de "
                    "scaling usando a métrica InvocationsPerInstance "
                    "do CloudWatch. Configure os limites mínimo e máximo "
                    "de instâncias."
                ),
                (
                    "O Amazon DynamoDB oferece modos de capacidade "
                    "on-demand e provisionada. O modo provisionado permite "
                    "configurar autoscaling para leitura e escrita."
                ),
                (
                    "O Amazon ECS permite configurar Service Auto Scaling "
                    "para ajustar automaticamente o número desejado de "
                    "tasks em um serviço baseado em métricas."
                ),
            ],
            expected_output=(
                "Para autoscaling em SageMaker: registrar o endpoint no "
                "Application Auto Scaling, definir política baseada em "
                "InvocationsPerInstance do CloudWatch, e configurar "
                "limites mínimo/máximo de instâncias."
            ),
            context=[
                (
                    "Para configurar autoscaling em endpoints SageMaker, "
                    "registre o endpoint no Application Auto Scaling e "
                    "defina uma política baseada em InvocationsPerInstance."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 5: Contexto Incompleto — Gap de informação
        # -----------------------------------------------------------------
        self._scenarios["incomplete_context"] = RAGTestScenario(
            scenario_id="incomplete_context",
            scenario_name="Contexto Incompleto — Gap de Recall",
            description=(
                "O retriever falha em recuperar todos os chunks necessários "
                "para uma resposta completa. O contexto cobre apenas parte "
                "da informação exigida pelo expected_output."
            ),
            input=(
                "Quais são as três estratégias de deployment suportadas "
                "pelo SageMaker para atualização de modelos em produção?"
            ),
            actual_output=(
                "O SageMaker suporta as seguintes estratégias de deployment "
                "para atualização de modelos: (1) Blue/Green deployment, "
                "que permite troca zero-downtime entre versões, e "
                "(2) Rolling deployment, que atualiza instâncias "
                "gradualmente. Não foram encontradas informações sobre "
                "outras estratégias no contexto disponível."
            ),
            retrieval_context=[
                (
                    "O SageMaker suporta Blue/Green deployment para "
                    "atualização de modelos em produção. Esta estratégia "
                    "cria um novo fleet de instâncias com a nova versão "
                    "do modelo e redireciona o tráfego quando validado, "
                    "garantindo zero-downtime."
                ),
                (
                    "O Rolling deployment no SageMaker atualiza instâncias "
                    "gradualmente, substituindo uma fração do fleet por "
                    "vez. Isso reduz o risco de impacto total em caso "
                    "de falha na nova versão."
                ),
            ],
            expected_output=(
                "As três estratégias de deployment do SageMaker são: "
                "(1) Blue/Green deployment com zero-downtime, "
                "(2) Rolling deployment com atualização gradual, e "
                "(3) Canary deployment que roteia uma pequena percentagem "
                "do tráfego para a nova versão antes do rollout completo."
            ),
            context=[
                (
                    "O SageMaker suporta Blue/Green deployment e Rolling "
                    "deployment para atualização de modelos."
                ),
            ],
        )

    # =========================================================================
    # CENÁRIOS AVANÇADOS (6-10)
    # =========================================================================

    def _register_advanced_scenarios(self) -> None:
        """Registra os 5 cenários avançados de edge cases."""

        # -----------------------------------------------------------------
        # CENÁRIO 6: Multi-Hop Reasoning — Raciocínio em cadeia
        # -----------------------------------------------------------------
        self._scenarios["multi_hop_reasoning"] = RAGTestScenario(
            scenario_id="multi_hop_reasoning",
            scenario_name="Multi-Hop Reasoning — Raciocínio Encadeado",
            description=(
                "A pergunta exige que o modelo conecte informações de "
                "múltiplos chunks em sequência lógica. Testa a capacidade "
                "de síntese e preservação de entidades entre 'saltos' "
                "de raciocínio. Falha comum: perda de entidade no 2o hop."
            ),
            input=(
                "Se eu treinar um modelo no SageMaker usando instâncias "
                "ml.p4d.24xlarge e depois fizer deploy em um endpoint "
                "com instâncias ml.g5.xlarge, qual será o impacto na "
                "latência de inferência comparado ao treinamento?"
            ),
            actual_output=(
                "As instâncias ml.p4d.24xlarge usadas no treinamento "
                "possuem 8 GPUs NVIDIA A100 com 40GB de memória cada, "
                "otimizadas para throughput massivo. Ao fazer deploy "
                "em ml.g5.xlarge, que possui 1 GPU NVIDIA A10G com 24GB, "
                "a latência de inferência individual será significativamente "
                "menor que o tempo de treinamento por epoch, pois a "
                "inferência processa um exemplo por vez ao invés de "
                "batches. Porém, o throughput total será reduzido pela "
                "menor capacidade de paralelismo da instância de deploy."
            ),
            retrieval_context=[
                (
                    "As instâncias ml.p4d.24xlarge do SageMaker possuem "
                    "8 GPUs NVIDIA A100 com 40GB de memória HBM2e cada, "
                    "totalizando 320GB de memória GPU. São otimizadas "
                    "para treinamento distribuído de modelos de grande "
                    "escala com alta demanda de throughput."
                ),
                (
                    "As instâncias ml.g5.xlarge oferecem 1 GPU NVIDIA A10G "
                    "com 24GB de memória GDDR6. São projetadas para "
                    "inferência de modelos de ML com boa relação "
                    "custo-benefício, oferecendo baixa latência para "
                    "requisições individuais."
                ),
                (
                    "A latência de inferência em endpoints SageMaker "
                    "depende do tamanho do modelo, da instância utilizada "
                    "e do tamanho do payload. Inferência processa uma "
                    "requisição por vez (ou micro-batches), enquanto "
                    "treinamento processa batches grandes em paralelo."
                ),
            ],
            expected_output=(
                "O treinamento em ml.p4d.24xlarge (8x A100) otimiza "
                "throughput com batches grandes. O deploy em ml.g5.xlarge "
                "(1x A10G) terá latência individual menor, mas throughput "
                "total reduzido pela menor capacidade de paralelismo."
            ),
            context=[
                (
                    "ml.p4d.24xlarge: 8 GPUs NVIDIA A100 40GB cada, "
                    "otimizadas para treinamento distribuído."
                ),
                (
                    "ml.g5.xlarge: 1 GPU NVIDIA A10G 24GB, otimizada "
                    "para inferência com boa relação custo-benefício."
                ),
                (
                    "Inferência processa requisições individuais enquanto "
                    "treinamento processa batches grandes em paralelo."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 7: Semantic Drift — Desvio semântico na resposta
        # -----------------------------------------------------------------
        self._scenarios["semantic_drift"] = RAGTestScenario(
            scenario_id="semantic_drift",
            scenario_name="Semantic Drift — Desvio Semântico Progressivo",
            description=(
                "A resposta começa correta mas gradualmente se desvia "
                "do tópico original, introduzindo informações de domínios "
                "adjacentes. Simula o fenômeno de 'topic drift' onde o "
                "modelo perde o foco após as primeiras sentenças."
            ),
            input=(
                "Como funciona o SageMaker Feature Store para "
                "gerenciamento de features de ML?"
            ),
            actual_output=(
                "O SageMaker Feature Store é um repositório centralizado "
                "para armazenar, compartilhar e gerenciar features de ML. "
                "Ele oferece uma Online Store para inferência em tempo "
                "real com latência de milissegundos e uma Offline Store "
                "baseada em S3 para treinamento em batch. "
                "Falando em armazenamento, o Amazon S3 é o serviço de "
                "armazenamento de objetos mais utilizado na AWS, "
                "oferecendo 99.999999999% de durabilidade. O S3 também "
                "se integra com o AWS Glue para catalogação de dados e "
                "com o Amazon Athena para consultas SQL serverless."
            ),
            retrieval_context=[
                (
                    "O SageMaker Feature Store é um repositório "
                    "centralizado e propositado para armazenar, "
                    "compartilhar e gerenciar features de Machine Learning. "
                    "Ele garante consistência entre treinamento e "
                    "inferência ao servir as mesmas features."
                ),
                (
                    "O Feature Store oferece dois modos de armazenamento: "
                    "a Online Store, que fornece acesso em tempo real com "
                    "latência de milissegundos para inferência, e a "
                    "Offline Store, que armazena dados históricos no "
                    "Amazon S3 para treinamento em batch e análise."
                ),
            ],
            expected_output=(
                "O SageMaker Feature Store é um repositório centralizado "
                "de features com Online Store (tempo real, baixa latência) "
                "e Offline Store (S3, treinamento batch), garantindo "
                "consistência entre treinamento e inferência."
            ),
            context=[
                (
                    "O SageMaker Feature Store é um repositório "
                    "centralizado para features de ML."
                ),
                (
                    "Oferece Online Store (tempo real) e Offline Store "
                    "(S3 para batch), garantindo consistência."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 8: Entidade Incorreta — Troca de entidades
        # -----------------------------------------------------------------
        self._scenarios["entity_swap"] = RAGTestScenario(
            scenario_id="entity_swap",
            scenario_name="Entity Swap — Troca de Entidades",
            description=(
                "O modelo confunde entidades similares, atribuindo "
                "características de um serviço a outro. Falha sutil "
                "e perigosa pois a resposta é sintaticamente correta "
                "mas factualmente errada. Comum em domínios com muitos "
                "serviços de nomes parecidos (ex: AWS)."
            ),
            input=(
                "Qual serviço da AWS é recomendado para orquestração "
                "de pipelines de ML com etapas de pré-processamento, "
                "treinamento e deployment?"
            ),
            actual_output=(
                "O AWS Step Functions é o serviço recomendado para "
                "orquestração de pipelines de ML completos. Ele permite "
                "definir workflows visuais com etapas de pré-processamento, "
                "treinamento e deployment de modelos, com integração "
                "nativa ao SageMaker para cada etapa do ciclo de vida."
            ),
            retrieval_context=[
                (
                    "O Amazon SageMaker Pipelines é o serviço recomendado "
                    "para orquestração de pipelines de ML. Ele permite "
                    "definir workflows de ML com etapas de pré-processamento, "
                    "treinamento, avaliação e deployment, integrado "
                    "nativamente ao ecossistema SageMaker."
                ),
                (
                    "O AWS Step Functions é um serviço de orquestração "
                    "serverless para workflows genéricos de aplicação. "
                    "Embora possa ser usado para ML, ele não possui a "
                    "integração nativa e as otimizações específicas "
                    "do SageMaker Pipelines."
                ),
            ],
            expected_output=(
                "O Amazon SageMaker Pipelines é o serviço recomendado "
                "para orquestração de pipelines de ML com integração "
                "nativa ao ecossistema SageMaker."
            ),
            context=[
                (
                    "O SageMaker Pipelines é o serviço recomendado para "
                    "orquestração de pipelines de ML."
                ),
                (
                    "O AWS Step Functions é para workflows genéricos, "
                    "sem otimizações específicas de ML."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 9: Resposta Segura — Conteúdo livre de toxicidade/bias
        # -----------------------------------------------------------------
        self._scenarios["safe_output"] = RAGTestScenario(
            scenario_id="safe_output",
            scenario_name="Safe Output — Conteúdo Seguro e Neutro",
            description=(
                "A resposta é factualmente correta, neutra e livre de "
                "conteúdo tóxico ou viés. Usado como baseline positivo "
                "para as métricas de segurança (Toxicity e Bias)."
            ),
            input=(
                "Quais tipos de instâncias o SageMaker suporta para "
                "inferência em tempo real?"
            ),
            actual_output=(
                "O SageMaker suporta diversos tipos de instâncias para "
                "inferência em tempo real, incluindo: instâncias CPU "
                "(séries ml.m5, ml.c5) para modelos leves, instâncias "
                "GPU (séries ml.g4dn, ml.g5, ml.p3) para modelos de "
                "deep learning, e instâncias com AWS Inferentia "
                "(ml.inf1, ml.inf2) otimizadas para inferência com "
                "melhor relação custo-performance."
            ),
            retrieval_context=[
                (
                    "O SageMaker suporta instâncias CPU (ml.m5, ml.c5), "
                    "GPU (ml.g4dn, ml.g5, ml.p3), e AWS Inferentia "
                    "(ml.inf1, ml.inf2) para inferência em tempo real. "
                    "A escolha depende do tamanho do modelo e requisitos "
                    "de latência."
                ),
            ],
            expected_output=(
                "O SageMaker suporta instâncias CPU (ml.m5, ml.c5), "
                "GPU (ml.g4dn, ml.g5, ml.p3) e Inferentia (ml.inf1, "
                "ml.inf2) para inferência real-time."
            ),
            context=[
                (
                    "O SageMaker suporta instâncias CPU, GPU e "
                    "Inferentia para inferência em tempo real."
                ),
            ],
        )

        # -----------------------------------------------------------------
        # CENÁRIO 10: Contradição Intra-Contexto — Chunks conflitantes
        # -----------------------------------------------------------------
        self._scenarios["contradictory_context"] = RAGTestScenario(
            scenario_id="contradictory_context",
            scenario_name="Contradição Intra-Contexto — Chunks Conflitantes",
            description=(
                "Os chunks recuperados contêm informações contraditórias "
                "entre si. Testa se o modelo lida com a ambiguidade sem "
                "fabricar uma resolução falsa. Edge case crítico em bases "
                "documentais com versões desatualizadas."
            ),
            input=(
                "Qual é o timeout máximo para endpoints SageMaker "
                "assíncronos?"
            ),
            actual_output=(
                "De acordo com os dados disponíveis, o timeout máximo "
                "para endpoints SageMaker assíncronos é de 3600 segundos "
                "(1 hora). Este limite pode ser configurado durante a "
                "criação do endpoint configuration."
            ),
            retrieval_context=[
                (
                    "Os endpoints SageMaker assíncronos possuem um timeout "
                    "máximo de 3600 segundos (1 hora) para processamento "
                    "de cada requisição."
                ),
                (
                    "A partir de 2024, o timeout máximo para endpoints "
                    "SageMaker assíncronos foi aumentado para 7200 "
                    "segundos (2 horas) em todas as regiões suportadas."
                ),
            ],
            expected_output=(
                "O timeout máximo para endpoints SageMaker assíncronos "
                "é de 7200 segundos (2 horas), atualizado em 2024."
            ),
            context=[
                (
                    "Endpoints assíncronos do SageMaker possuem timeout "
                    "de 3600 segundos."
                ),
                (
                    "A partir de 2024, o timeout foi aumentado para "
                    "7200 segundos."
                ),
            ],
        )
