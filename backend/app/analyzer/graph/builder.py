"""Build repository dependency graphs from parsed Python modules."""

from __future__ import annotations

from app.analyzer.parsing.models import ParsedModule

from .dependency_graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyType,
)


def resolve_relative_import(
    source_module: str,
    imported_module: str,
) -> str:
    """
    Resolve a relative import against the importing module.

    Examples:
        source_module="app.analyzer.parsing.python_parser"
        imported_module=".models"
        result="app.analyzer.parsing.models"

        source_module="app.analyzer.parsing.python_parser"
        imported_module="..graph"
        result="app.analyzer.graph"

    Returns an empty string if the import tries to move above the
    available package hierarchy.
    """

    if not imported_module.startswith("."):
        return imported_module

    relative_level = len(imported_module) - len(
        imported_module.lstrip(".")
    )

    remaining_module = imported_module[relative_level:]

    source_parts = source_module.split(".")

    # Remove the current module name so resolution begins
    # from the package containing that module.
    package_parts = source_parts[:-1]

    levels_to_move_up = relative_level - 1

    if levels_to_move_up > len(package_parts):
        return ""

    if levels_to_move_up:
        package_parts = package_parts[:-levels_to_move_up]

    if remaining_module:
        package_parts.extend(remaining_module.split("."))

    return ".".join(package_parts)


class DependencyGraphBuilder:
    """
    Build a repository-level dependency graph from parsed modules.
    """

    def build(
        self,
        modules: list[ParsedModule],
    ) -> DependencyGraph:
        """
        Build and return a graph containing module nodes and import edges.

        Nodes are added before edges so imports can be classified as
        internal or external using the complete repository module set.
        """

        graph = DependencyGraph()

        self._add_module_nodes(
            graph=graph,
            modules=modules,
        )

        self._add_import_edges(
            graph=graph,
            modules=modules,
        )

        return graph

    @staticmethod
    def _add_module_nodes(
        graph: DependencyGraph,
        modules: list[ParsedModule],
    ) -> None:
        """
        Add one graph node for every parsed Python module.
        """

        for module in modules:
            graph.add_node(
                DependencyNode(
                    module_name=module.module_name,
                    file_path=str(module.path),
                )
            )

    def _add_import_edges(
        self,
        graph: DependencyGraph,
        modules: list[ParsedModule],
    ) -> None:
        """
        Add one dependency edge for every imported module.
        """

        internal_modules = set(graph.nodes)

        for module in modules:
            for imported in module.imports:
                target_module = resolve_relative_import(
                    source_module=module.module_name,
                    imported_module=imported.module,
                )

                dependency_type = self._classify_dependency(
                    imported_module=target_module,
                    internal_modules=internal_modules,
                )

                graph.add_edge(
                    DependencyEdge(
                        source=module.module_name,
                        target=target_module,
                        dependency_type=dependency_type,
                    )
                )

    @staticmethod
    def _classify_dependency(
        imported_module: str,
        internal_modules: set[str],
    ) -> DependencyType:
        """
        Classify an imported module as internal, external, or unresolved.
        """

        if not imported_module:
            return DependencyType.UNRESOLVED

        if imported_module in internal_modules:
            return DependencyType.INTERNAL

        # Treat a package import as internal when the repository contains
        # modules inside that package.
        #
        # Example:
        # imported_module="app.services"
        # repository module="app.services.users"
        if any(
            module_name.startswith(f"{imported_module}.")
            for module_name in internal_modules
        ):
            return DependencyType.INTERNAL

        return DependencyType.EXTERNAL