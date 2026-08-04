from app.analyzer.parsing.models import ParsedModule

from .dependency_graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyType,
)


class DependencyGraphBuilder:
    def build(
        self,
        modules: list[ParsedModule],
    ) -> DependencyGraph:
        graph = DependencyGraph()

        for module in modules:
            graph.add_node(
                DependencyNode(
                    module_name=module.module_name,
                    file_path=module.file_path,
                )
            )

        internal_modules = set(graph.nodes)

        for module in modules:
            for imported in module.imports:
                graph.add_edge(
                    DependencyEdge(
                        source=module.module_name,
                        target=imported.module,
                        dependency_type=self._classify_dependency(
                            imported.module,
                            internal_modules,
                        ),
                    )
                )

        return graph

    @staticmethod
    def _classify_dependency(
        imported_module: str,
        internal_modules: set[str],
    ) -> DependencyType:
        if not imported_module:
            return DependencyType.UNRESOLVED

        if imported_module in internal_modules:
            return DependencyType.INTERNAL

        if any(
            module.startswith(f"{imported_module}.")
            for module in internal_modules
        ):
            return DependencyType.INTERNAL

        return DependencyType.EXTERNAL