def build_architecture_prompt(
    architecture_context: str,
) -> str:
    """Build the prompt used for repository architecture analysis."""

    return f"""
Analyze the software architecture described below.

Base your analysis only on the provided repository information.

Evaluate:

- overall architectural structure
- module organization
- dependency relationships
- coupling between modules
- circular dependencies
- isolated modules
- maintainability
- potential architectural risks
- practical opportunities for improvement

Do not claim that the repository contains something unless it can be
reasonably inferred from the provided architecture information.

Repository Architecture:

{architecture_context}
""".strip()