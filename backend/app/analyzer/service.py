"""Main application service for repository analysis."""

from pathlib import Path

from app.analyzer.graph import (
    DependencyGraph,
    DependencyGraphAnalyzer,
    DependencyGraphBuilder,
)
from app.analyzer.parsing.models import ParsedModule
from app.analyzer.parsing.python_parser import PythonParser
from app.analyzer.repository.scanner import RepositoryScanner


class PythonAnalysisService:
    """Coordinate parsing and repository analysis."""

    def __init__(
        self,
        parser: PythonParser | None = None,
        scanner: RepositoryScanner | None = None,
        graph_builder: DependencyGraphBuilder | None = None,
    ) -> None:
        self.parser = parser or PythonParser()
        self.scanner = scanner or RepositoryScanner()
        self.graph_builder = (
            graph_builder or DependencyGraphBuilder()
        )

    def analyze_repository(
        self,
        repository_path: Path,
    ) -> tuple[
        list[ParsedModule],
        DependencyGraph,
        DependencyGraphAnalyzer,
    ]:
        files = self.scanner.scan(repository_path)

        modules: list[ParsedModule] = []

        for file_path in files:
            source = file_path.read_text(
                encoding="utf-8"
            )

            parsed_module = self.parser.parse(
                source=source,
                path=file_path,
                repository_root=repository_path,
            )

            modules.append(parsed_module)

        graph = self.graph_builder.build(modules)

        analyzer = DependencyGraphAnalyzer(graph)

        return modules, graph, analyzer