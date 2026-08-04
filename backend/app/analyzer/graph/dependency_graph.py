from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DependencyType(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class DependencyNode:
    """
    Represents one Python module/file in the repository.
    """

    module_name: str
    file_path: str


@dataclass(frozen=True)
class DependencyEdge:
    """
    Represents a directed dependency.

    Example:
        app.main -> app.services.users
    """

    source: str
    target: str
    dependency_type: DependencyType


@dataclass
class DependencyGraph:
    """
    Stores repository modules and the dependencies between them.
    """

    nodes: dict[str, DependencyNode] = field(default_factory=dict)
    edges: set[DependencyEdge] = field(default_factory=set)

    def add_node(self, node: DependencyNode) -> None:
        """
        Add a module to the graph.

        Adding a node with the same module name replaces the existing node.
        """

        self.nodes[node.module_name] = node

    def add_edge(self, edge: DependencyEdge) -> None:
        """
        Add a dependency originating from an existing module.
        """

        if edge.source not in self.nodes:
            raise ValueError(
                f"Source module {edge.source!r} does not exist in the graph."
            )

        self.edges.add(edge)

    def has_node(self, module_name: str) -> bool:
        return module_name in self.nodes

    def get_node(self, module_name: str) -> DependencyNode | None:
        return self.nodes.get(module_name)

    def dependencies_of(
        self,
        module_name: str,
    ) -> list[DependencyEdge]:
        """
        Return all outgoing dependencies for a module.
        """

        self._validate_module_exists(module_name)

        return sorted(
            (
                edge
                for edge in self.edges
                if edge.source == module_name
            ),
            key=lambda edge: (
                edge.target,
                edge.dependency_type.value,
            ),
        )

    def dependents_of(
        self,
        module_name: str,
    ) -> list[DependencyEdge]:
        """
        Return all dependencies pointing to a module.
        """

        self._validate_module_exists(module_name)

        return sorted(
            (
                edge
                for edge in self.edges
                if edge.target == module_name
            ),
            key=lambda edge: (
                edge.source,
                edge.dependency_type.value,
            ),
        )

    def internal_edges(self) -> list[DependencyEdge]:
        return self.edges_by_type(DependencyType.INTERNAL)

    def external_edges(self) -> list[DependencyEdge]:
        return self.edges_by_type(DependencyType.EXTERNAL)

    def unresolved_edges(self) -> list[DependencyEdge]:
        return self.edges_by_type(DependencyType.UNRESOLVED)

    def edges_by_type(
        self,
        dependency_type: DependencyType,
    ) -> list[DependencyEdge]:
        return sorted(
            (
                edge
                for edge in self.edges
                if edge.dependency_type == dependency_type
            ),
            key=lambda edge: (
                edge.source,
                edge.target,
            ),
        )

    def _validate_module_exists(self, module_name: str) -> None:
        if module_name not in self.nodes:
            raise ValueError(
                f"Module {module_name!r} does not exist in the graph."
            )