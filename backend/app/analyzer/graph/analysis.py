from __future__ import annotations

from dataclasses import dataclass

from .dependency_graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyType,
)
@dataclass(frozen=True)
class ModuleMetrics:
    """
    Summary of how one module interacts with the repository.
    """

    module_name: str
    outgoing_dependencies: int
    incoming_dependencies: int
    internal_dependencies: int
    external_dependencies: int
    unresolved_dependencies: int


class DependencyGraphAnalyzer:
    """
    Performs analysis on a completed DependencyGraph.
    """

    def __init__(self, graph: DependencyGraph) -> None:
        self.graph = graph

    def module_metrics(
        self,
        module_name: str,
    ) -> ModuleMetrics:
        """
        Calculate dependency counts for one module.
        """

        if not self.graph.has_node(module_name):
            raise ValueError(
                f"Module {module_name!r} does not exist in the graph."
            )

        outgoing = self.graph.dependencies_of(module_name)
        incoming = self.graph.dependents_of(module_name)

        return ModuleMetrics(
            module_name=module_name,
            outgoing_dependencies=len(outgoing),
            incoming_dependencies=len(incoming),
            internal_dependencies=self._count_dependency_type(
                outgoing,
                DependencyType.INTERNAL,
            ),
            external_dependencies=self._count_dependency_type(
                outgoing,
                DependencyType.EXTERNAL,
            ),
            unresolved_dependencies=self._count_dependency_type(
                outgoing,
                DependencyType.UNRESOLVED,
            ),
        )

    def all_module_metrics(self) -> list[ModuleMetrics]:
        """
        Return metrics for every module in the graph.
        """

        return [
            self.module_metrics(module_name)
            for module_name in sorted(self.graph.nodes)
        ]

    def most_depended_on_modules(
        self,
        limit: int = 10,
    ) -> list[ModuleMetrics]:
        """
        Return modules with the most incoming dependencies.
        """

        if limit < 1:
            raise ValueError("limit must be at least 1.")

        metrics = self.all_module_metrics()

        return sorted(
            metrics,
            key=lambda metric: (
                -metric.incoming_dependencies,
                metric.module_name,
            ),
        )[:limit]

    def isolated_modules(self) -> list[str]:
        """
        Find modules with no incoming or outgoing dependencies.
        """

        isolated: list[str] = []

        for module_name in self.graph.nodes:
            metrics = self.module_metrics(module_name)

            if (
                metrics.incoming_dependencies == 0
                and metrics.outgoing_dependencies == 0
            ):
                isolated.append(module_name)

        return sorted(isolated)

    def find_cycles(self) -> list[list[str]]:
        """
        Find cycles between internal repository modules.

        Example:
            app.a -> app.b -> app.c -> app.a
        """

        adjacency = self._build_internal_adjacency()

        state: dict[str, int] = {
            module_name: 0
            for module_name in self.graph.nodes
        }

        current_path: list[str] = []
        cycles: list[list[str]] = []
        seen_cycles: set[tuple[str, ...]] = set()

        def visit(module_name: str) -> None:
            state[module_name] = 1
            current_path.append(module_name)

            for dependency in sorted(adjacency[module_name]):
                if state[dependency] == 0:
                    visit(dependency)

                elif state[dependency] == 1:
                    cycle_start = current_path.index(dependency)

                    cycle = (
                        current_path[cycle_start:]
                        + [dependency]
                    )

                    normalized_cycle = self._normalize_cycle(cycle)

                    if normalized_cycle not in seen_cycles:
                        seen_cycles.add(normalized_cycle)
                        cycles.append(list(normalized_cycle))

            current_path.pop()
            state[module_name] = 2

        for module_name in sorted(self.graph.nodes):
            if state[module_name] == 0:
                visit(module_name)

        return cycles

    def _build_internal_adjacency(
        self,
    ) -> dict[str, set[str]]:
        """
        Build an adjacency list containing internal dependencies only.
        """

        adjacency: dict[str, set[str]] = {
            module_name: set()
            for module_name in self.graph.nodes
        }

        for edge in self.graph.internal_edges():
            if edge.target in self.graph.nodes:
                adjacency[edge.source].add(edge.target)

        return adjacency

    @staticmethod
    def _count_dependency_type(
        edges: list[DependencyEdge],
        dependency_type: DependencyType,
    ) -> int:
        return sum(
            edge.dependency_type == dependency_type
            for edge in edges
        )

    @staticmethod
    def _normalize_cycle(
        cycle: list[str],
    ) -> tuple[str, ...]:
        """
        Ensure the same cycle always has the same representation.

        Example:
            app.b -> app.c -> app.a -> app.b

        becomes:
            app.a -> app.b -> app.c -> app.a
        """

        cycle_nodes = cycle[:-1]

        if not cycle_nodes:
            return tuple(cycle)

        smallest_index = min(
            range(len(cycle_nodes)),
            key=lambda index: cycle_nodes[index],
        )

        rotated = (
            cycle_nodes[smallest_index:]
            + cycle_nodes[:smallest_index]
        )

        return tuple(rotated + [rotated[0]])