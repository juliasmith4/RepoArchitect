from app.analyzer.ai.models import ArchitectureInsights


def test_creates_architecture_insights():
    insights = ArchitectureInsights(
        summary="The repository uses a modular architecture.",
        strengths=[
            "Clear separation between services.",
        ],
        concerns=[
            "One circular dependency exists.",
        ],
        recommendations=[
            "Remove the circular dependency.",
        ],
    )

    assert insights.summary == (
        "The repository uses a modular architecture."
    )

    assert insights.strengths == [
        "Clear separation between services."
    ]

    assert insights.concerns == [
        "One circular dependency exists."
    ]

    assert insights.recommendations == [
        "Remove the circular dependency."
    ]


def test_architecture_insights_lists_default_to_empty():
    insights = ArchitectureInsights(
        summary="Repository architecture analysis."
    )

    assert insights.strengths == []
    assert insights.concerns == []
    assert insights.recommendations == []