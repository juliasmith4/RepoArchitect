from app.analyzer.graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyGraphAnalyzer,
    DependencyNode,
    DependencyType,
    ModuleMetrics,
)

def create_graph() -> DependencyGraph:
    graph = DependencyGraph()

    for module_name in (
        "app.main",
        "app.services.users",
        "app.database",
        "app.unused",
    ):
        graph.add_node(
            DependencyNode(
                module_name=module_name,
                file_path=f"{module_name.replace('.', '/')}.py",
            )
        )

    graph.add_edge(
        DependencyEdge(
            source="app.main",
            target="app.services.users",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.services.users",
            target="app.database",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.main",
            target="fastapi",
            dependency_type=DependencyType.EXTERNAL,
        )
    )

    return graph


def test_calculates_module_metrics() -> None:
    graph = create_graph()
    analyzer = DependencyGraphAnalyzer(graph)

    metrics = analyzer.module_metrics("app.main")

    assert metrics.outgoing_dependencies == 2
    assert metrics.incoming_dependencies == 0
    assert metrics.internal_dependencies == 1
    assert metrics.external_dependencies == 1


def test_finds_most_depended_on_modules() -> None:
    graph = create_graph()
    analyzer = DependencyGraphAnalyzer(graph)

    results = analyzer.most_depended_on_modules()

    assert results[0].module_name in {
        "app.services.users",
        "app.database",
    }

    assert results[0].incoming_dependencies == 1


def test_finds_isolated_modules() -> None:
    graph = create_graph()
    analyzer = DependencyGraphAnalyzer(graph)

    assert analyzer.isolated_modules() == ["app.unused"]


def test_finds_internal_dependency_cycle() -> None:
    graph = DependencyGraph()

    for module_name in ("app.a", "app.b", "app.c"):
        graph.add_node(
            DependencyNode(
                module_name=module_name,
                file_path=f"{module_name.replace('.', '/')}.py",
            )
        )

    graph.add_edge(
        DependencyEdge(
            source="app.a",
            target="app.b",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.b",
            target="app.c",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.c",
            target="app.a",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    analyzer = DependencyGraphAnalyzer(graph)

    assert analyzer.find_cycles() == [
        ["app.a", "app.b", "app.c", "app.a"]
    ]