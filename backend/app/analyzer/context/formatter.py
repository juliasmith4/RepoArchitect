from .models import ArchitectureContext


class ArchitectureContextFormatter:
    """Convert architecture context into LLM-friendly text."""

    def format(
        self,
        context: ArchitectureContext,
    ) -> str:
        sections = [
            self._format_summary(context),
            self._format_modules(context),
            self._format_dependencies(context),
            self._format_findings(context),
        ]

        return "\n\n".join(sections)

    def _format_summary(
        self,
        context: ArchitectureContext,
    ) -> str:
        return "\n".join(
            [
                "Repository Summary:",
                f"- Files: {context.file_count}",
                f"- Functions: {context.function_count}",
                f"- Classes: {context.class_count}",
                f"- Methods: {context.method_count}",
            ]
        )

    def _format_modules(
        self,
        context: ArchitectureContext,
    ) -> str:
        lines = ["Modules:"]

        if not context.modules:
            lines.append("- None")
        else:
            lines.extend(
                f"- {module}"
                for module in context.modules
            )

        return "\n".join(lines)

    def _format_dependencies(
        self,
        context: ArchitectureContext,
    ) -> str:
        lines = ["Dependencies:"]

        lines.append("Internal:")
        lines.extend(
            f"- {dependency}"
            for dependency in context.internal_dependencies
        )

        lines.append("External:")
        lines.extend(
            f"- {dependency}"
            for dependency in context.external_dependencies
        )

        lines.append("Unresolved:")
        lines.extend(
            f"- {dependency}"
            for dependency in context.unresolved_dependencies
        )

        return "\n".join(lines)

    def _format_findings(
        self,
        context: ArchitectureContext,
    ) -> str:
        lines = ["Architectural Findings:"]

        lines.append("Most depended-on modules:")
        lines.extend(
            f"- {module}"
            for module in context.most_depended_on_modules
        )

        lines.append("Isolated modules:")
        lines.extend(
            f"- {module}"
            for module in context.isolated_modules
        )

        lines.append("Circular dependencies:")

        for cycle in context.circular_dependencies:
            lines.append(
                f"- {' -> '.join(cycle)}"
            )

        return "\n".join(lines)