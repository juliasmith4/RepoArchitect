"""Architecture finding detection."""

from dataclasses import dataclass
from enum import Enum

from app.analyzer.graph import (
    DependencyGraph,
    DependencyGraphAnalyzer,
)


class FindingSeverity(str, Enum):
    """Severity level for an architecture finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FindingType(str, Enum):
    """Types of architecture findings RepoArchitect can detect."""

    CIRCULAR_DEPENDENCY = "circular_dependency"
    HIGH_OUTGOING_COUPLING = "high_outgoing_coupling"
    HIGH_INCOMING_COUPLING = "high_incoming_coupling"
    ISOLATED_MODULE = "isolated_module"
    UNRESOLVED_DEPENDENCY = "unresolved_dependency"


@dataclass(slots=True, frozen=True)
class ArchitectureFinding:
    """One architecture issue or observation."""

    finding_type: FindingType
    severity: FindingSeverity
    message: str
    modules: tuple[str, ...]


class ArchitectureFindingDetector:
    """Detect architecture findings from a dependency graph."""

    def __init__(
        self,
        high_outgoing_threshold: int = 8,
        high_incoming_threshold: int = 8,
    ) -> None:
        self.high_outgoing_threshold = high_outgoing_threshold
        self.high_incoming_threshold = high_incoming_threshold

    def detect(
        self,
        graph: DependencyGraph,
    ) -> list[ArchitectureFinding]:
        """Run all architecture finding detectors."""

        analyzer = DependencyGraphAnalyzer(graph)

        findings: list[ArchitectureFinding] = []

        findings.extend(
            self._detect_cycles(analyzer)
        )

        findings.extend(
            self._detect_high_coupling(
                analyzer=analyzer,
                graph=graph,
            )
        )

        findings.extend(
            self._detect_isolated_modules(
                analyzer=analyzer,
                graph=graph,
            )
        )

        findings.extend(
            self._detect_unresolved_dependencies(graph)
        )

        return findings

    @staticmethod
    def _detect_cycles(
        analyzer: DependencyGraphAnalyzer,
    ) -> list[ArchitectureFinding]:
        """Detect circular internal module dependencies."""

        findings: list[ArchitectureFinding] = []

        for cycle in analyzer.find_cycles():
            modules = tuple(cycle[:-1])

            findings.append(
                ArchitectureFinding(
                    finding_type=FindingType.CIRCULAR_DEPENDENCY,
                    severity=FindingSeverity.ERROR,
                    message=(
                        "Circular dependency detected: "
                        + " -> ".join(cycle)
                    ),
                    modules=modules,
                )
            )

        return findings

    def _detect_high_coupling(
        self,
        analyzer: DependencyGraphAnalyzer,
        graph: DependencyGraph,
    ) -> list[ArchitectureFinding]:
        """Detect modules with unusually high dependency counts."""

        findings: list[ArchitectureFinding] = []

        for module_name in graph.nodes:
            metrics = analyzer.module_metrics(module_name)

            if (
                metrics.outgoing_dependencies
                >= self.high_outgoing_threshold
            ):
                findings.append(
                    ArchitectureFinding(
                        finding_type=(
                            FindingType.HIGH_OUTGOING_COUPLING
                        ),
                        severity=FindingSeverity.WARNING,
                        message=(
                            f"{module_name} depends on "
                            f"{metrics.outgoing_dependencies} "
                            "modules."
                        ),
                        modules=(module_name,),
                    )
                )

            if (
                metrics.incoming_dependencies
                >= self.high_incoming_threshold
            ):
                findings.append(
                    ArchitectureFinding(
                        finding_type=(
                            FindingType.HIGH_INCOMING_COUPLING
                        ),
                        severity=FindingSeverity.WARNING,
                        message=(
                            f"{module_name} is depended on by "
                            f"{metrics.incoming_dependencies} "
                            "modules."
                        ),
                        modules=(module_name,),
                    )
                )

        return findings

    @staticmethod
    def _detect_isolated_modules(
        analyzer: DependencyGraphAnalyzer,
        graph: DependencyGraph,
    ) -> list[ArchitectureFinding]:
        """
        Detect isolated modules.

        Empty package __init__.py files are ignored because they are
        commonly present only to define package structure.
        """

        findings: list[ArchitectureFinding] = []

        for module_name in analyzer.isolated_modules():
            node = graph.get_node(module_name)

            if node is None:
                continue

            if node.file_path.endswith("__init__.py"):
                continue

            findings.append(
                ArchitectureFinding(
                    finding_type=FindingType.ISOLATED_MODULE,
                    severity=FindingSeverity.INFO,
                    message=(
                        f"{module_name} has no incoming or "
                        "outgoing module dependencies."
                    ),
                    modules=(module_name,),
                )
            )

        return findings

    @staticmethod
    def _detect_unresolved_dependencies(
        graph: DependencyGraph,
    ) -> list[ArchitectureFinding]:
        """Detect dependencies that could not be resolved."""

        findings: list[ArchitectureFinding] = []

        for edge in graph.unresolved_edges():
            findings.append(
                ArchitectureFinding(
                    finding_type=(
                        FindingType.UNRESOLVED_DEPENDENCY
                    ),
                    severity=FindingSeverity.WARNING,
                    message=(
                        f"{edge.source} contains an unresolved "
                        f"dependency on {edge.target!r}."
                    ),
                    modules=(edge.source,),
                )
            )

        return findings