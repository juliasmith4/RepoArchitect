from unittest.mock import MagicMock

import pytest

from app.analyzer.ai.analyzer import GeminiArchitectureAnalyzer
from app.analyzer.ai.models import ArchitectureInsights
from app.analyzer.context.models import ArchitectureContext


def test_analyzes_architecture_context():
    expected_insights = ArchitectureInsights(
        summary="The repository has a modular architecture.",
        strengths=[
            "Clear module separation.",
        ],
        concerns=[
            "A circular dependency exists.",
        ],
        recommendations=[
            "Remove the circular dependency.",
        ],
    )

    mock_response = MagicMock()
    mock_response.parsed = expected_insights

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    analyzer = GeminiArchitectureAnalyzer(
        client=mock_client,
        model="test-model",
    )

    context = ArchitectureContext(
        file_count=5,
        function_count=10,
        class_count=2,
        method_count=6,
        modules=[
            "app.main",
            "app.services.users",
        ],
        internal_dependencies=[
            "app.main -> app.services.users",
        ],
        external_dependencies=[
            "app.main -> fastapi",
        ],
    )

    result = analyzer.analyze(context)

    assert result == expected_insights

    mock_client.models.generate_content.assert_called_once()


def test_raises_when_gemini_returns_no_parsed_response():
    mock_response = MagicMock()
    mock_response.parsed = None

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    analyzer = GeminiArchitectureAnalyzer(
        client=mock_client,
        model="test-model",
    )

    context = ArchitectureContext()

    with pytest.raises(
        ValueError,
        match="Gemini did not return structured architecture insights.",
    ):
        analyzer.analyze(context)