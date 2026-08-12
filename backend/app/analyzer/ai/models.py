from pydantic import BaseModel, Field


class ArchitectureInsights(BaseModel):
    """AI-generated analysis of a repository's architecture."""

    summary: str = Field(
        description="Concise overview of the repository architecture."
    )

    strengths: list[str] = Field(
        default_factory=list,
        description="Architectural strengths found in the repository.",
    )

    concerns: list[str] = Field(
        default_factory=list,
        description="Architectural or maintainability concerns.",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Practical recommendations for improving the architecture.",
    )