from google import genai

from app.analyzer.context.formatter import ArchitectureContextFormatter
from app.analyzer.context.models import ArchitectureContext

from .models import ArchitectureInsights
from .prompt import build_architecture_prompt


class GeminiArchitectureAnalyzer:
    """Generate architecture insights using Gemini."""

    def __init__(
        self,
        client: genai.Client,
        model: str,
    ) -> None:
        self.client = client
        self.model = model
        self.formatter = ArchitectureContextFormatter()

    def analyze(
        self,
        context: ArchitectureContext,
    ) -> ArchitectureInsights:
        formatted_context = self.formatter.format(context)

        prompt = build_architecture_prompt(
            formatted_context
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ArchitectureInsights,
            },
        )

        if response.parsed is None:
            raise ValueError(
                "Gemini did not return structured architecture insights."
            )

        return response.parsed