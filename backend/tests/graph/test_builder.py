from app.analyzer.graph import (
    DependencyGraphBuilder,
    DependencyType,
)
from app.analyzer.parsing.models import (
    ImportInfo,
    ParsedModule,
)


def test_builds_nodes_from_parsed_modules() -> None:
    modules = [
        ParsedModule(
            file_path="app/main.py",
            module_name="app.main",
        ),
        ParsedModule(
            file_path="app/services/users.py",
            module_name="app.services.users",
        ),
    ]

    graph = DependencyGraphBuilder().build(modules)

    assert set(graph.nodes) == {
        "app.main",
        "app.services.users",
    }


def test_builds_internal_and_external_edges() -> None:
    modules = [
        ParsedModule(
            file_path="app/main.py",
            module_name="app.main",
            imports=[
                ImportInfo(
                    module="app.services.users",
                    names=["get_user"],
                    alias=None,
                    line_number=1,
                    is_from_import=True,
                ),
                ImportInfo(
                    module="fastapi",
                    names=[],
                    alias=None,
                    line_number=2,
                    is_from_import=False,
                ),
            ],
        ),
        ParsedModule(
            file_path="app/services/users.py",
            module_name="app.services.users",
        ),
    ]

    graph = DependencyGraphBuilder().build(modules)

    dependencies = graph.dependencies_of("app.main")

    internal_edge = next(
        edge
        for edge in dependencies
        if edge.target == "app.services.users"
    )

    external_edge = next(
        edge
        for edge in dependencies
        if edge.target == "fastapi"
    )

    assert internal_edge.dependency_type == DependencyType.INTERNAL
    assert external_edge.dependency_type == DependencyType.EXTERNAL