"""Repository-level architecture metrics."""

from dataclasses import dataclass

from app.analyzer.graph import (
    DependencyGraph,
    DependencyGraphAnalyzer,
)


@dataclass(slots=True, frozen=True)
class RepositoryMetrics:
    """Summary metrics for a repository dependency graph."""

    module_count: int
    dependency_count: int
    internal_dependency_count: int
    external_dependency_count: int
    unresolved_dependency_count: int
    isolated_module_count: int
    circular_dependency_count: int


class RepositoryMetricsCalculator:
    """Calculate repository-level dependency metrics."""

    def calculate(
        self,
        graph: DependencyGraph,
    ) -> RepositoryMetrics:
        analyzer = DependencyGraphAnalyzer(graph)

        isolated_modules = analyzer.isolated_modules()
        cycles = analyzer.find_cycles()

        return RepositoryMetrics(
            module_count=len(graph.nodes),
            dependency_count=len(graph.edges),
            internal_dependency_count=len(
                graph.internal_edges()
            ),
            external_dependency_count=len(
                graph.external_edges()
            ),
            unresolved_dependency_count=len(
                graph.unresolved_edges()
            ),
            isolated_module_count=len(
                isolated_modules
            ),
            circular_dependency_count=len(
                cycles
            ),
        )