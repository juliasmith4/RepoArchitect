from app.analyzer.ai.prompt import build_architecture_prompt


def test_builds_architecture_prompt():
    architecture_context = """
Repository Summary:
- Files: 10
- Functions: 24

Modules:
- app.main
- app.services.users

Circular dependencies:
- app.a -> app.b -> app.a
""".strip()

    prompt = build_architecture_prompt(
        architecture_context
    )

    assert "Analyze the software architecture" in prompt
    assert "app.main" in prompt
    assert "app.services.users" in prompt
    assert "app.a -> app.b -> app.a" in prompt


def test_prompt_contains_analysis_guidance():
    prompt = build_architecture_prompt(
        "Repository Summary:\n- Files: 5"
    )

    assert "dependency relationships" in prompt
    assert "coupling between modules" in prompt
    assert "circular dependencies" in prompt
    assert "maintainability" in prompt
    assert "practical opportunities for improvement" in prompt