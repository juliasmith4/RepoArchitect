from app.analyzer.parsing.models import ParsedModule

from .models import ArchitectureContext


class ArchitectureContextBuilder:
    """Build repository-level architecture context from parsed modules."""

    def build(
        self,
        parsed_modules: list[ParsedModule],
    ) -> ArchitectureContext:
        context = ArchitectureContext()

        for module in parsed_modules:
            if not module.was_parsed_successfully:
                continue

            context.file_count += 1
            context.function_count += module.function_count
            context.class_count += module.class_count
            context.method_count += module.method_count

            context.modules.append(module.module_name)

        return context