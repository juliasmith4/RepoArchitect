"""Convert parsed Python structures into architectural dependencies."""

import ast

from app.analyzer.parsing.models import (
    ParsedAssignment,
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

        dependencies.extend(
            self._analyze_calls(
                function=function,
                source=source,
            )
        )

        dependencies.extend(
            self._analyze_assignments(
                function=function,
                source=source,
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

    def _analyze_calls(
        self,
        *,
        function: ParsedFunction,
        source: str,
    ) -> list[Dependency]:
        """Convert parsed calls into call dependencies."""

        dependencies: list[Dependency] = []

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

    def _analyze_assignments(
        self,
        *,
        function: ParsedFunction,
        source: str,
    ) -> list[Dependency]:
        """Identify dependencies created through assignments."""

        dependencies: list[Dependency] = []

        for assignment in function.assignments:
            dependency = self._assignment_to_dependency(
                function=function,
                assignment=assignment,
                source=source,
            )

            if dependency is not None:
                dependencies.append(dependency)

        return dependencies

    def _assignment_to_dependency(
        self,
        *,
        function: ParsedFunction,
        assignment: ParsedAssignment,
        source: str,
    ) -> Dependency | None:
        """Convert a constructor assignment into a dependency."""

        if function.name != "__init__":
            return None

        if not assignment.is_instance_attribute:
            return None

        constructor_name = self._get_constructor_name(
            assignment.value
        )

        if constructor_name is None:
            return None

        class_source = function.parent_class or source

        return Dependency(
            source=class_source,
            target=constructor_name,
            dependency_type="instantiates",
            line_number=assignment.line_number,
        )

    def _get_constructor_name(
        self,
        value: str | None,
    ) -> str | None:
        """Return the called constructor name from an expression."""

        if value is None:
            return None

        try:
            expression = ast.parse(
                value,
                mode="eval",
            ).body
        except SyntaxError:
            return None

        if not isinstance(expression, ast.Call):
            return None

        return self._callable_name(expression.func)

    def _callable_name(
        self,
        node: ast.AST,
    ) -> str | None:
        """Return the readable name of a callable expression."""

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parent_name = self._callable_name(node.value)

            if parent_name is None:
                return node.attr

            return f"{parent_name}.{node.attr}"

        return None

    def _get_function_name(
        self,
        function: ParsedFunction,
    ) -> str:
        """Return a qualified function or method name."""

        if function.parent_class is not None:
            return f"{function.parent_class}.{function.name}"

        return function.name

def analyze_module(
    self,
    *,
    functions: list[ParsedFunction],
    classes: list[ParsedClass],
) -> list[Dependency]:
    """Extract dependencies from all module-level functions and classes."""

    dependencies: list[Dependency] = []

    for function in functions:
        dependencies.extend(
            self.analyze_function(function)
        )

    for parsed_class in classes:
        dependencies.extend(
            self.analyze_class(parsed_class)
        )

    return dependencies