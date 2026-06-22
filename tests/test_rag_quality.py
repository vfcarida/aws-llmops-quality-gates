"""
Test RAG Quality — Suíte de 14 Asserções de Qualidade para Pipeline RAG.

Este módulo implementa uma barreira de qualidade automatizada (Quality Gate)
utilizando o framework DeepEval como LLM-as-a-Judge. Cada teste é uma
asserção programática que força falhas (build breaks) na esteira de CI/CD
caso detecte regressões de qualidade.

Distribuição dos 14 testes:
    ┌─────────────────────────────────────┬───────┬──────────────┐
    │ Categoria                           │ Qtd   │ Thresholds   │
    ├─────────────────────────────────────┼───────┼──────────────┤
    │ Faithfulness / Groundedness         │   3   │ 0.85 — 0.90  │
    │ Answer Relevance                    │   3   │ 0.85 — 0.90  │
    │ Context Precision                   │   3   │ 0.85 — 0.90  │
    │ Context Recall                      │   2   │ 0.85 — 0.90  │
    │ Toxicity / Bias / Hallucination     │   2   │ 0.85         │
    │ Context Relevancy                   │   1   │ 0.85         │
    └─────────────────────────────────────┴───────┴──────────────┘

Execução:
    deepeval test run tests/test_rag_quality.py -v
    pytest tests/test_rag_quality.py -v --tb=long

Autor: MLOps Quality Gate Pipeline
Compatível com: deepeval >= 4.0 | pytest >= 8.0 | AWS Bedrock (Claude)
"""

from __future__ import annotations

import logging

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    ToxicityMetric,
)
from deepeval.models import AmazonBedrockModel
from deepeval.test_case import LLMTestCase

logger = logging.getLogger("rag_quality_gate")


# =============================================================================
# HELPER — Log de resultado da métrica
# =============================================================================


def _log_metric_result(metric_name: str, metric: object) -> None:
    """Loga o score e reason de uma métrica para observabilidade CI/CD.

    Args:
        metric_name: Nome legível da métrica.
        metric: Instância da métrica após avaliação (possui .score e .reason).
    """
    score = getattr(metric, "score", "N/A")
    reason = getattr(metric, "reason", "N/A")
    logger.info(
        "[%s] Score: %s | Reason: %s",
        metric_name,
        score,
        reason,
    )


# =============================================================================
# BLOCO 1: FAITHFULNESS / GROUNDEDNESS (3 testes)
# =============================================================================
# Validações focadas em garantir que a resposta gerada não contém nenhuma
# informação que não esteja estritamente presente no retrieval_context.
# =============================================================================


@pytest.mark.faithfulness
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_faithfulness_high_grounding(
    happy_path_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """FAITH-01: Resposta perfeitamente alinhada ao contexto.

    Cenário: Happy path — todos os claims da resposta são rastreáveis
    aos chunks recuperados.

    Threshold: 0.90 (rigoroso — exige quase perfeita aderência).
    Falha se: O modelo adicionou qualquer informação não presente no contexto.
    """
    metric = FaithfulnessMetric(threshold=0.90, model=bedrock_judge)
    assert_test(happy_path_case, [metric])
    _log_metric_result("FAITH-01 High Grounding", metric)


@pytest.mark.faithfulness
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_faithfulness_rejects_hallucinated_facts(
    hallucinated_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """FAITH-02: Detecta fatos fabricados na resposta.

    Cenário: A resposta contém informações inventadas (plano gratuito,
    desconto de 90%, garantia de preço até 2030) que NÃO estão no contexto.

    Design TDD: Este teste DEVE FALHAR quando executado contra o cenário
    de alucinação, provando que o quality gate efetivamente barra respostas
    com fatos fabricados. Um score BAIXO de faithfulness é o resultado
    esperado.

    Threshold: 0.85 — O cenário alucinado deve produzir score << 0.85.
    """
    metric = FaithfulnessMetric(threshold=0.85, model=bedrock_judge)
    # NOTE: Este teste é projetado para FALHAR com o cenário hallucinated.
    # Em produção, isso causaria um build break — exatamente o comportamento
    # desejado de um quality gate.
    assert_test(hallucinated_case, [metric])
    _log_metric_result("FAITH-02 Hallucinated Facts", metric)


@pytest.mark.faithfulness
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_faithfulness_entity_swap_detection(
    entity_swap_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """FAITH-03: Detecta troca de entidades na resposta.

    Cenário: O modelo atribui características do SageMaker Pipelines ao
    AWS Step Functions. A resposta é sintaticamente coerente mas factualmente
    incorreta em relação ao contexto recuperado.

    Threshold: 0.85 — Entidades trocadas devem reduzir o score.
    """
    metric = FaithfulnessMetric(threshold=0.85, model=bedrock_judge)
    assert_test(entity_swap_case, [metric])
    _log_metric_result("FAITH-03 Entity Swap", metric)


# =============================================================================
# BLOCO 2: ANSWER RELEVANCE (3 testes)
# =============================================================================
# Asserções para penalizar respostas evasivas, garantindo que o modelo
# responda de forma direta e concisa ao input original.
# =============================================================================


@pytest.mark.answer_relevance
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_answer_relevance_direct_response(
    happy_path_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """RELEV-01: Resposta direta e concisa à pergunta.

    Cenário: Happy path — a resposta endereça exatamente o que foi
    perguntado, sem rodeios ou disclaimers desnecessários.

    Threshold: 0.90 — Alta exigência de diretividade.
    """
    metric = AnswerRelevancyMetric(threshold=0.90, model=bedrock_judge)
    assert_test(happy_path_case, [metric])
    _log_metric_result("RELEV-01 Direct Response", metric)


@pytest.mark.answer_relevance
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_answer_relevance_penalizes_evasive(
    evasive_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """RELEV-02: Penaliza respostas evasivas e genéricas.

    Cenário: O modelo retorna uma resposta tangencial que não endereça
    a pergunta específica do usuário (limite de payload 6MB), preferindo
    dar uma visão geral genérica do SageMaker.

    Threshold: 0.85 — Evasão deve produzir score baixo.
    """
    metric = AnswerRelevancyMetric(threshold=0.85, model=bedrock_judge)
    assert_test(evasive_case, [metric])
    _log_metric_result("RELEV-02 Evasive Penalization", metric)


@pytest.mark.answer_relevance
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_answer_relevance_complex_multi_hop_query(
    multi_hop_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """RELEV-03: Relevância em perguntas multi-hop complexas.

    Cenário: Pergunta que exige conectar informações de múltiplos chunks
    (especificações de ml.p4d vs ml.g5 + impacto na latência). Valida
    que a resposta mantém relevância mesmo em raciocínio encadeado.

    Threshold: 0.85 — Tolera ligeira perda por complexidade, mas
    exige que a resposta permaneça on-topic.
    """
    metric = AnswerRelevancyMetric(threshold=0.85, model=bedrock_judge)
    assert_test(multi_hop_case, [metric])
    _log_metric_result("RELEV-03 Multi-Hop Query", metric)


# =============================================================================
# BLOCO 3: CONTEXT PRECISION (3 testes)
# =============================================================================
# Testes focados na camada de recuperação, avaliando se os chunks de maior
# ranqueamento realmente contêm a informação necessária.
# =============================================================================


@pytest.mark.context_precision
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_context_precision_relevant_ranking(
    happy_path_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """PREC-01: Chunks relevantes dominam o ranking.

    Cenário: Happy path — todos os chunks recuperados são altamente
    relevantes e corretamente ranqueados para a pergunta.

    Threshold: 0.90 — Ranking ideal deve pontuar alto.
    """
    metric = ContextualPrecisionMetric(threshold=0.90, model=bedrock_judge)
    assert_test(happy_path_case, [metric])
    _log_metric_result("PREC-01 Relevant Ranking", metric)


@pytest.mark.context_precision
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_context_precision_noisy_context(
    noisy_context_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """PREC-02: Penaliza ranking com chunks irrelevantes.

    Cenário: O retriever retorna 5 chunks, mas apenas 1 contém a
    informação relevante (autoscaling SageMaker). Os outros 4 são
    sobre EC2, Lambda, DynamoDB e ECS — ruído informacional.

    Threshold: 0.85 — O ruído deve degradar a precisão contextual.
    """
    metric = ContextualPrecisionMetric(threshold=0.85, model=bedrock_judge)
    assert_test(noisy_context_case, [metric])
    _log_metric_result("PREC-02 Noisy Context", metric)


@pytest.mark.context_precision
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_context_precision_contradictory_chunks(
    contradictory_context_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """PREC-03: Avalia precisão com chunks contraditórios.

    Cenário: Dois chunks com informações conflitantes sobre o timeout
    de endpoints assíncronos (3600s vs 7200s). Avalia se a métrica de
    precisão captura a ambiguidade no ranking.

    Threshold: 0.85 — Contradição pode impactar a precisão.
    """
    metric = ContextualPrecisionMetric(threshold=0.85, model=bedrock_judge)
    assert_test(contradictory_context_case, [metric])
    _log_metric_result("PREC-03 Contradictory Chunks", metric)


# =============================================================================
# BLOCO 4: CONTEXT RECALL (2 testes)
# =============================================================================
# Validam se todo o conhecimento exigido para uma resposta perfeita
# (expected_output) foi efetivamente recuperado da base de dados.
# =============================================================================


@pytest.mark.context_recall
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_context_recall_full_coverage(
    happy_path_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """RECALL-01: Cobertura total do expected_output no contexto.

    Cenário: Happy path — o retrieval_context contém todas as informações
    necessárias para responder perfeitamente à pergunta. O expected_output
    deve ser integralmente coberto pelos chunks.

    Threshold: 0.90 — Exige cobertura quase completa.
    """
    metric = ContextualRecallMetric(threshold=0.90, model=bedrock_judge)
    assert_test(happy_path_case, [metric])
    _log_metric_result("RECALL-01 Full Coverage", metric)


@pytest.mark.context_recall
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_context_recall_partial_gap(
    incomplete_context_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """RECALL-02: Detecta gap parcial na recuperação.

    Cenário: A pergunta exige 3 estratégias de deployment, mas o contexto
    só cobre 2 (Blue/Green e Rolling). A 3ª (Canary) está ausente.
    O expected_output inclui as 3 — o recall deve refletir o gap.

    Threshold: 0.85 — O gap parcial deve degradar o recall.
    """
    metric = ContextualRecallMetric(threshold=0.85, model=bedrock_judge)
    assert_test(incomplete_context_case, [metric])
    _log_metric_result("RECALL-02 Partial Gap", metric)


# =============================================================================
# BLOCO 5: TOXICITY / BIAS / HALLUCINATION (2 testes)
# =============================================================================
# Filtros binários de segurança avaliando se a resposta é segura ou
# se introduziu fatos fabricados.
# =============================================================================


@pytest.mark.safety
@pytest.mark.quality_gate
def test_no_hallucination_in_output(
    happy_path_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """SAFE-01: Filtro binário de alucinação.

    Cenário: Happy path — a resposta deve ser classificada como NÃO
    alucinada, pois todos os fatos são rastreáveis ao contexto.

    Nota: HallucinationMetric usa o campo `context` (não retrieval_context)
    para avaliar se o actual_output contradiz os fatos providos.

    Threshold: 0.85 — Tolerância mínima para falsos positivos.
    """
    metric = HallucinationMetric(threshold=0.85, model=bedrock_judge)
    assert_test(happy_path_case, [metric])
    _log_metric_result("SAFE-01 Hallucination Filter", metric)


@pytest.mark.safety
@pytest.mark.quality_gate
def test_output_safety_no_toxicity_or_bias(
    safe_output_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """SAFE-02: Filtro de segurança — toxicidade e viés.

    Cenário: Resposta técnica neutra sobre tipos de instâncias.
    Deve pontuar baixo em toxicidade e viés.

    Avalia ambas as métricas em sequência. Qualquer falha é um
    build break imediato.

    Threshold: 0.85 para ambas as métricas.
    """
    toxicity_metric = ToxicityMetric(threshold=0.85, model=bedrock_judge)
    bias_metric = BiasMetric(threshold=0.85, model=bedrock_judge)

    assert_test(safe_output_case, [toxicity_metric, bias_metric])

    _log_metric_result("SAFE-02 Toxicity", toxicity_metric)
    _log_metric_result("SAFE-02 Bias", bias_metric)


# =============================================================================
# BLOCO 6: CONTEXT RELEVANCY (1 teste)
# =============================================================================
# Mede a densidade do ruído informacional nos nós recuperados,
# penalizando a injeção de tokens irrelevantes no prompt.
# =============================================================================


@pytest.mark.context_relevancy
@pytest.mark.rag_triad
@pytest.mark.quality_gate
def test_context_relevancy_low_noise(
    happy_path_case: LLMTestCase,
    bedrock_judge: AmazonBedrockModel,
) -> None:
    """CTX-REL-01: Alta densidade de informação relevante nos chunks.

    Cenário: Happy path — todos os chunks recuperados contêm informação
    diretamente relevante à pergunta, sem tokens desnecessários.

    Essa métrica complementa Context Precision ao avaliar não apenas
    o ranking, mas a qualidade interna de cada chunk.

    Threshold: 0.85 — Penaliza chunks inflados com informação tangencial.
    """
    metric = ContextualRelevancyMetric(threshold=0.85, model=bedrock_judge)
    assert_test(happy_path_case, [metric])
    _log_metric_result("CTX-REL-01 Low Noise", metric)
