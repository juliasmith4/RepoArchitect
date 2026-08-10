from dataclasses import dataclass
from pathlib import Path
from app.analyzer.repository.cloner import RepositoryCloner

from app.analyzer.findings import (
    ArchitectureFinding,
    ArchitectureFindingDetector,
)
from app.analyzer.graph import (
    DependencyGraph,
    DependencyGraphBuilder,
)
from app.analyzer.metrics import (
    RepositoryMetrics,
    RepositoryMetricsCalculator,
)
from app.analyzer.parsing.models import ParsedModule
from app.analyzer.parsing.python_parser import PythonParser
from app.analyzer.repository.scanner import RepositoryScanner


@dataclass(slots=True)
class RepositoryAnalysisResult:
    """Complete result of analyzing a repository."""

    modules: list[ParsedModule]
    graph: DependencyGraph
    metrics: RepositoryMetrics
    findings: list[ArchitectureFinding]


class PythonAnalysisService:
    def __init__(
        self,
        parser: PythonParser | None = None,
        scanner: RepositoryScanner | None = None,
        cloner: RepositoryCloner | None = None,
        graph_builder: DependencyGraphBuilder | None = None,
        metrics_calculator: RepositoryMetricsCalculator | None = None,
        finding_detector: ArchitectureFindingDetector | None = None,
    ) -> None:
        self.parser = parser or PythonParser()
        self.scanner = scanner or RepositoryScanner()
        self.cloner = cloner or RepositoryCloner()
        self.graph_builder = (
            graph_builder or DependencyGraphBuilder()
        )
        self.metrics_calculator = (
            metrics_calculator or RepositoryMetricsCalculator()
        )
        self.finding_detector = (
            finding_detector or ArchitectureFindingDetector()
        )

    def analyze_repository(
        self,
        repository_path: Path,
    ) -> RepositoryAnalysisResult:
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

        metrics = self.metrics_calculator.calculate(graph)

        findings = self.finding_detector.detect(graph)

        return RepositoryAnalysisResult(
            modules=modules,
            graph=graph,
            metrics=metrics,
            findings=findings,
        )

    def analyze_repository_url(
        self,
        repository_url: str,
    ) -> RepositoryAnalysisResult:
        """Clone and analyze a remote GitHub repository."""

        cloned_repository = self.cloner.clone(
            repository_url
        )

        try:
            return self.analyze_repository(
                cloned_repository.path
            )
        finally:
            self.cloner.cleanup(
                cloned_repository.path.parent
            )