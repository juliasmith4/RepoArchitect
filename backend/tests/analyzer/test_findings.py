from app.analyzer.findings import (
    ArchitectureFindingDetector,
    FindingSeverity,
    FindingType,
)
from app.analyzer.graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyType,
)


def add_node(
    graph: DependencyGraph,
    module_name: str,
) -> None:
    graph.add_node(
        DependencyNode(
            module_name=module_name,
            file_path=f"{module_name.replace('.', '/')}.py",
        )
    )


def test_detects_circular_dependency() -> None:
    graph = DependencyGraph()

    for module_name in ("a", "b", "c"):
        add_node(graph, module_name)

    graph.add_edge(
        DependencyEdge(
            source="a",
            target="b",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="b",
            target="c",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="c",
            target="a",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    findings = ArchitectureFindingDetector().detect(graph)

    circular_findings = [
        finding
        for finding in findings
        if finding.finding_type
        == FindingType.CIRCULAR_DEPENDENCY
    ]

    assert len(circular_findings) == 1

    finding = circular_findings[0]

    assert finding.severity == FindingSeverity.ERROR
    assert finding.modules == ("a", "b", "c")
    assert "a -> b -> c -> a" in finding.message


def test_detects_high_outgoing_coupling() -> None:
    graph = DependencyGraph()

    add_node(graph, "main")

    for module_name in (
        "service_a",
        "service_b",
        "service_c",
    ):
        add_node(graph, module_name)

        graph.add_edge(
            DependencyEdge(
                source="main",
                target=module_name,
                dependency_type=DependencyType.INTERNAL,
            )
        )

    detector = ArchitectureFindingDetector(
        high_outgoing_threshold=3,
        high_incoming_threshold=10,
    )

    findings = detector.detect(graph)

    coupling_findings = [
        finding
        for finding in findings
        if finding.finding_type
        == FindingType.HIGH_OUTGOING_COUPLING
    ]

    assert len(coupling_findings) == 1

    finding = coupling_findings[0]

    assert finding.severity == FindingSeverity.WARNING
    assert finding.modules == ("main",)
    assert "3 modules" in finding.message


def test_detects_high_incoming_coupling() -> None:
    graph = DependencyGraph()

    add_node(graph, "shared")

    for module_name in (
        "service_a",
        "service_b",
        "service_c",
    ):
        add_node(graph, module_name)

        graph.add_edge(
            DependencyEdge(
                source=module_name,
                target="shared",
                dependency_type=DependencyType.INTERNAL,
            )
        )

    detector = ArchitectureFindingDetector(
        high_outgoing_threshold=10,
        high_incoming_threshold=3,
    )

    findings = detector.detect(graph)

    coupling_findings = [
        finding
        for finding in findings
        if finding.finding_type
        == FindingType.HIGH_INCOMING_COUPLING
    ]

    assert len(coupling_findings) == 1

    finding = coupling_findings[0]

    assert finding.severity == FindingSeverity.WARNING
    assert finding.modules == ("shared",)
    assert "3 modules" in finding.message


def test_detects_isolated_module() -> None:
    graph = DependencyGraph()

    add_node(graph, "main")
    add_node(graph, "unused")

    graph.add_edge(
        DependencyEdge(
            source="main",
            target="requests",
            dependency_type=DependencyType.EXTERNAL,
        )
    )

    findings = ArchitectureFindingDetector().detect(graph)

    isolated_findings = [
        finding
        for finding in findings
        if finding.finding_type
        == FindingType.ISOLATED_MODULE
    ]

    assert len(isolated_findings) == 1

    finding = isolated_findings[0]

    assert finding.severity == FindingSeverity.INFO
    assert finding.modules == ("unused",)


def test_detects_unresolved_dependency() -> None:
    graph = DependencyGraph()

    add_node(graph, "main")

    graph.add_edge(
        DependencyEdge(
            source="main",
            target="unknown.module",
            dependency_type=DependencyType.UNRESOLVED,
        )
    )

    findings = ArchitectureFindingDetector().detect(graph)

    unresolved_findings = [
        finding
        for finding in findings
        if finding.finding_type
        == FindingType.UNRESOLVED_DEPENDENCY
    ]

    assert len(unresolved_findings) == 1

    finding = unresolved_findings[0]

    assert finding.severity == FindingSeverity.WARNING
    assert finding.modules == ("main",)
    assert "unknown.module" in finding.message


def test_returns_no_problem_findings_for_simple_connected_graph() -> None:
    graph = DependencyGraph()

    add_node(graph, "main")
    add_node(graph, "service")

    graph.add_edge(
        DependencyEdge(
            source="main",
            target="service",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    detector = ArchitectureFindingDetector(
        high_outgoing_threshold=5,
        high_incoming_threshold=5,
    )

    findings = detector.detect(graph)

    assert findings == []