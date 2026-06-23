"""
Conftest — Fixtures e hooks para a suíte de Quality Gates RAG.

Configura:
    - AWS Bedrock (Claude) como LLM-as-a-Judge
    - Fixtures de pipeline e cenários pré-carregados
    - Hook para extrair metric.reason em falhas de CI/CD

Autor: MLOps Quality Gate Pipeline
Compatível com: deepeval >= 4.0 | pytest >= 8.0
"""

from __future__ import annotations

import logging
import os
from typing import Any, Generator

import pytest
from deepeval.models import AmazonBedrockModel
from deepeval.test_case import LLMTestCase

from rag_pipeline_mock import RAGPipelineMock, RAGTestScenario

logger = logging.getLogger("rag_quality_gate")


# =============================================================================
# AWS BEDROCK — LLM-as-a-Judge Configuration
# =============================================================================


def get_bedrock_judge() -> AmazonBedrockModel:
    """Instancia o modelo Bedrock (Claude) para atuar como juiz.

    O modelo pode ser configurado via variáveis de ambiente:
        - BEDROCK_MODEL_ID: ID do modelo no Bedrock (default: Claude 3.5 Sonnet)
        - BEDROCK_REGION: Região AWS (default: us-east-1)

    Returns:
        AmazonBedrockModel configurado para avaliação.

    Note:
        Requer AWS credentials configuradas no ambiente:
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN (opcional)
    """
    model_id = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
    )
    region = os.getenv("BEDROCK_REGION", "us-east-1")

    logger.info(
        "Inicializando Bedrock Judge: model=%s, region=%s",
        model_id,
        region,
    )

    return AmazonBedrockModel(
        model=model_id,
        region=region,
        generation_kwargs={
            "temperature": 0,
            "max_tokens": 4096,
        },
    )


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def bedrock_judge() -> AmazonBedrockModel:
    """Fixture de sessão: modelo Bedrock compartilhado entre todos os testes.

    Scope 'session' garante que o modelo é instanciado apenas uma vez,
    otimizando o custo de inicialização.
    """
    return get_bedrock_judge()


@pytest.fixture(scope="session")
def rag_pipeline() -> RAGPipelineMock:
    """Fixture de sessão: instância do pipeline RAG mock."""
    return RAGPipelineMock()


# ---------------------------------------------------------------------------
# Helpers para construção de LLMTestCase a partir de cenários
# ---------------------------------------------------------------------------


def build_test_case(scenario: RAGTestScenario) -> LLMTestCase:
    """Constrói um LLMTestCase do DeepEval a partir de um RAGTestScenario.

    Args:
        scenario: Cenário de teste com dados do pipeline.

    Returns:
        LLMTestCase configurado para avaliação.
    """
    return LLMTestCase(
        input=scenario.input,
        actual_output=scenario.actual_output,
        expected_output=scenario.expected_output,
        retrieval_context=scenario.retrieval_context,
        context=scenario.context if scenario.context else None,
    )


@pytest.fixture(scope="session")
def happy_path_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário happy path."""
    return build_test_case(rag_pipeline.get_scenario("happy_path"))


@pytest.fixture(scope="session")
def hallucinated_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de alucinação."""
    return build_test_case(rag_pipeline.get_scenario("hallucinated_response"))


@pytest.fixture(scope="session")
def evasive_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de resposta evasiva."""
    return build_test_case(rag_pipeline.get_scenario("evasive_response"))


@pytest.fixture(scope="session")
def noisy_context_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de contexto ruidoso."""
    return build_test_case(rag_pipeline.get_scenario("noisy_context"))


@pytest.fixture(scope="session")
def incomplete_context_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de contexto incompleto."""
    return build_test_case(rag_pipeline.get_scenario("incomplete_context"))


@pytest.fixture(scope="session")
def multi_hop_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de raciocínio multi-hop."""
    return build_test_case(rag_pipeline.get_scenario("multi_hop_reasoning"))


@pytest.fixture(scope="session")
def semantic_drift_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de desvio semântico."""
    return build_test_case(rag_pipeline.get_scenario("semantic_drift"))


@pytest.fixture(scope="session")
def entity_swap_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de troca de entidades."""
    return build_test_case(rag_pipeline.get_scenario("entity_swap"))


@pytest.fixture(scope="session")
def safe_output_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de output seguro."""
    return build_test_case(rag_pipeline.get_scenario("safe_output"))


@pytest.fixture(scope="session")
def contradictory_context_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de contexto contraditório."""
    return build_test_case(rag_pipeline.get_scenario("contradictory_context"))


@pytest.fixture(scope="session")
def prompt_injection_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de prompt injection."""
    return build_test_case(rag_pipeline.get_scenario("prompt_injection"))


@pytest.fixture(scope="session")
def out_of_domain_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de resposta fora de domínio."""
    return build_test_case(rag_pipeline.get_scenario("out_of_domain"))


@pytest.fixture(scope="session")
def toxic_output_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de saída tóxica."""
    return build_test_case(rag_pipeline.get_scenario("toxic_output"))


@pytest.fixture(scope="session")
def biased_output_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de saída enviesada."""
    return build_test_case(rag_pipeline.get_scenario("biased_output"))


@pytest.fixture(scope="session")
def formatting_failure_case(rag_pipeline: RAGPipelineMock) -> LLMTestCase:
    """LLMTestCase para o cenário de quebra de formatação JSON."""
    return build_test_case(rag_pipeline.get_scenario("formatting_failure"))


# =============================================================================
# HOOK — Extração de metric.reason para CI/CD Logs
# =============================================================================


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[Any]
) -> Generator[None, None, None]:
    """Hook que captura metric.reason do DeepEval em falhas de teste.

    Quando um teste falha, o hook extrai a explicação legível gerada pelo
    LLM-as-a-Judge e a injeta nos logs do pytest, tornando o motivo da
    falha visível nos logs do CI/CD (GitHub Actions, CodePipeline, etc.).

    A razão da falha é adicionada como uma seção extra no relatório de teste.
    """
    outcome = yield
    report = outcome.get_result()  # type: ignore[attr-defined]

    if report.when == "call" and report.failed:
        # Tenta extrair informações de métrica da mensagem de erro
        if hasattr(call, "excinfo") and call.excinfo is not None:
            exc_value = call.excinfo.value
            error_message = str(exc_value)

            # Log estruturado para CI/CD
            logger.error(
                "\n"
                "╔══════════════════════════════════════════════════════════╗\n"
                "║       QUALITY GATE FAILURE — RAG ASSERTION BROKE        ║\n"
                "╠══════════════════════════════════════════════════════════╣\n"
                "║ Test: %-48s ║\n"
                "╠══════════════════════════════════════════════════════════╣\n"
                "║ Reason:                                                  ║\n"
                "║ %s\n"
                "╚══════════════════════════════════════════════════════════╝",
                item.name,
                error_message,
            )

            # Adiciona a razão como seção extra no relatório
            extra_info = (
                f"\n{'=' * 60}\n"
                f"🚨 QUALITY GATE FAILURE DETAILS\n"
                f"{'=' * 60}\n"
                f"Test: {item.name}\n"
                f"Error: {error_message}\n"
                f"{'=' * 60}\n"
            )
            report.sections.append(("Quality Gate Failure", extra_info))
