"""Convert parsed Python structures into architectural dependencies."""

from app.analyzer.parsing.models import (
    ParsedClass,
    ParsedFunction,
)

from .models import Dependency


class DependencyAnalyzer:
    """Identify dependencies from parsed Python structures."""

    def analyze_function(
        self,
        function: ParsedFunction,
    ) -> list[Dependency]:
        """Extract dependencies from one function or method."""

        dependencies: list[Dependency] = []

        source = self._get_function_name(function)

        for call in function.calls:
            dependencies.append(
                Dependency(
                    source=source,
                    target=call.name,
                    dependency_type="calls",
                    line_number=call.line_number,
                )
            )

        return dependencies

    def analyze_class(
        self,
        parsed_class: ParsedClass,
    ) -> list[Dependency]:
        """Extract dependencies from all methods in a class."""

        dependencies: list[Dependency] = []

        for method in parsed_class.methods:
            dependencies.extend(
                self.analyze_function(method)
            )

        return dependencies

    def _get_function_name(
        self,
        function: ParsedFunction,
    ) -> str:
        """Return a qualified function or method name."""

        if function.parent_class is not None:
            return f"{function.parent_class}.{function.name}"

        return function.name