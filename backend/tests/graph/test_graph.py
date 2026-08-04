from app.analyzer.graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyType,
)


def test_adds_node() -> None:
    graph = DependencyGraph()

    node = DependencyNode(
        module_name="app.main",
        file_path="app/main.py",
    )

    graph.add_node(node)

    assert graph.has_node("app.main")
    assert graph.get_node("app.main") == node


def test_adds_dependency_edge() -> None:
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.main",
            file_path="app/main.py",
        )
    )

    edge = DependencyEdge(
        source="app.main",
        target="app.services.users",
        dependency_type=DependencyType.INTERNAL,
    )

    graph.add_edge(edge)

    dependencies = graph.dependencies_of("app.main")

    assert dependencies == [edge]


def test_returns_dependents() -> None:
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.main",
            file_path="app/main.py",
        )
    )

    graph.add_node(
        DependencyNode(
            module_name="app.services.users",
            file_path="app/services/users.py",
        )
    )

    edge = DependencyEdge(
        source="app.main",
        target="app.services.users",
        dependency_type=DependencyType.INTERNAL,
    )

    graph.add_edge(edge)

    dependents = graph.dependents_of("app.services.users")

    assert dependents == [edge]


def test_filters_edges_by_dependency_type() -> None:
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.main",
            file_path="app/main.py",
        )
    )

    internal_edge = DependencyEdge(
        source="app.main",
        target="app.services.users",
        dependency_type=DependencyType.INTERNAL,
    )

    external_edge = DependencyEdge(
        source="app.main",
        target="fastapi",
        dependency_type=DependencyType.EXTERNAL,
    )

    graph.add_edge(internal_edge)
    graph.add_edge(external_edge)

    assert graph.internal_edges() == [internal_edge]
    assert graph.external_edges() == [external_edge]


def test_rejects_edge_with_missing_source() -> None:
    graph = DependencyGraph()

    edge = DependencyEdge(
        source="app.missing",
        target="fastapi",
        dependency_type=DependencyType.EXTERNAL,
    )

    try:
        graph.add_edge(edge)
    except ValueError as error:
        assert "app.missing" in str(error)
    else:
        raise AssertionError("Expected graph.add_edge() to raise ValueError")