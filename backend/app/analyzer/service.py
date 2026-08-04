"""High-level service for analyzing Python source code."""

import ast
from dataclasses import dataclass

from app.analyzer.dependencies.analyzer import DependencyAnalyzer
from app.analyzer.dependencies.models import (
    Dependency,
    ResolvedDependency,
)
from app.analyzer.dependencies.resolver import DependencyResolver
from app.analyzer.parsing.models import (
    ImportInfo,
    ParsedClass,
    ParsedFunction,
)
from app.analyzer.parsing.visitor import PythonAstVisitor


@dataclass
class ModuleAnalysisResult:
    """Complete analysis result for one Python module."""

    imports: list[ImportInfo]
    functions: list[ParsedFunction]
    classes: list[ParsedClass]
    dependencies: list[Dependency]
    resolved_dependencies: list[ResolvedDependency]


class PythonAnalysisService:
    """Run the complete Python module analysis pipeline."""

    def __init__(
        self,
        *,
        dependency_analyzer: DependencyAnalyzer | None = None,
        dependency_resolver: DependencyResolver | None = None,
    ) -> None:
        self._dependency_analyzer = (
            dependency_analyzer or DependencyAnalyzer()
        )
        self._dependency_resolver = (
            dependency_resolver or DependencyResolver()
        )

    def analyze_source(
        self,
        source_code: str,
    ) -> ModuleAnalysisResult:
        """Analyze Python source code from start to finish."""

        syntax_tree = ast.parse(source_code)

        visitor = PythonAstVisitor()
        visitor.visit(syntax_tree)

        dependencies = self._dependency_analyzer.analyze_module(
            functions=visitor.functions,
            classes=visitor.classes,
        )

        resolved_dependencies = (
            self._dependency_resolver.resolve_dependencies(
                dependencies=dependencies,
                imports=visitor.imports,
                functions=visitor.functions,
                classes=visitor.classes,
            )
        )

        return ModuleAnalysisResult(
            imports=visitor.imports,
            functions=visitor.functions,
            classes=visitor.classes,
            dependencies=dependencies,
            resolved_dependencies=resolved_dependencies,
        )