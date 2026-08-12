from pathlib import Path

from app.analyzer.context import ArchitectureContextBuilder
from app.analyzer.graph.dependency_graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyType,
)
from app.analyzer.parsing.models import (
    ParsedClass,
    ParsedFunction,
    ParsedModule,
)


def test_builds_architecture_context():
    parsed_modules = [
        ParsedModule(
            path=Path("app/main.py"),
            module_name="app.main",
            functions=[
                ParsedFunction(name="main"),
            ],
            classes=[
                ParsedClass(
                    name="Application",
                    methods=[
                        ParsedFunction(
                            name="run",
                            is_method=True,
                            parent_class="Application",
                        ),
                    ],
                ),
            ],
        ),
        ParsedModule(
            path=Path("app/services/analyzer.py"),
            module_name="app.services.analyzer",
            functions=[
                ParsedFunction(name="analyze"),
                ParsedFunction(name="load_repository"),
            ],
        ),
    ]

    builder = ArchitectureContextBuilder()

    context = builder.build(parsed_modules)

    assert context.file_count == 2
    assert context.function_count == 3
    assert context.class_count == 1
    assert context.method_count == 1
    assert context.modules == [
        "app.main",
        "app.services.analyzer",
    ]

def test_builds_empty_architecture_context():
    builder = ArchitectureContextBuilder()

    context = builder.build([])

    assert context.file_count == 0
    assert context.function_count == 0
    assert context.class_count == 0
    assert context.method_count == 0

    assert context.modules == []

    assert context.internal_dependencies == []
    assert context.external_dependencies == []
    assert context.unresolved_dependencies == []

    assert context.most_depended_on_modules == []
    assert context.isolated_modules == []
    assert context.circular_dependencies == []
def test_skips_modules_with_parse_errors():
    parsed_modules = [
        ParsedModule(
            path=Path("app/main.py"),
            module_name="app.main",
        ),
        ParsedModule(
            path=Path("app/broken.py"),
            module_name="app.broken",
            parse_error="invalid syntax",
        ),
    ]

    builder = ArchitectureContextBuilder()

    context = builder.build(parsed_modules)

    assert context.file_count == 1
    assert context.modules == [
        "app.main",
    ]


def test_adds_internal_dependencies():
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

    graph.add_edge(
        DependencyEdge(
            source="app.main",
            target="app.services.users",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    builder = ArchitectureContextBuilder()

    context = builder.build(
        parsed_modules=[],
        dependency_graph=graph,
    )

    assert context.internal_dependencies == [
        "app.main -> app.services.users"
    ]


def test_adds_external_dependencies():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.main",
            file_path="app/main.py",
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.main",
            target="fastapi",
            dependency_type=DependencyType.EXTERNAL,
        )
    )

    builder = ArchitectureContextBuilder()

    context = builder.build(
        parsed_modules=[],
        dependency_graph=graph,
    )

    assert context.external_dependencies == [
        "app.main -> fastapi"
    ]


def test_adds_unresolved_dependencies():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.main",
            file_path="app/main.py",
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.main",
            target="unknown_package",
            dependency_type=DependencyType.UNRESOLVED,
        )
    )

    builder = ArchitectureContextBuilder()

    context = builder.build(
        parsed_modules=[],
        dependency_graph=graph,
    )

    assert context.unresolved_dependencies == [
        "app.main -> unknown_package"
    ]
def test_adds_most_depended_on_modules():
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

    graph.add_node(
        DependencyNode(
            module_name="app.services.auth",
            file_path="app/services/auth.py",
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
            source="app.services.auth",
            target="app.services.users",
            dependency_type=DependencyType.INTERNAL,
        )
    )

    builder = ArchitectureContextBuilder()

    context = builder.build(
        parsed_modules=[],
        dependency_graph=graph,
    )

    assert context.most_depended_on_modules == [
        "app.services.users"
    ]
def test_adds_isolated_modules():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.main",
            file_path="app/main.py",
        )
    )

    graph.add_node(
        DependencyNode(
            module_name="app.unused",
            file_path="app/unused.py",
        )
    )

    graph.add_edge(
        DependencyEdge(
            source="app.main",
            target="fastapi",
            dependency_type=DependencyType.EXTERNAL,
        )
    )

    builder = ArchitectureContextBuilder()

    context = builder.build(
        parsed_modules=[],
        dependency_graph=graph,
    )

    assert context.isolated_modules == [
        "app.unused"
    ]
def test_adds_circular_dependencies():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            module_name="app.a",
            file_path="app/a.py",
        )
    )

    graph.add_node(
        DependencyNode(
            module_name="app.b",
            file_path="app/b.py",
        )
    )

    graph.add_node(
        DependencyNode(
            module_name="app.c",
            file_path="app/c.py",
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

    builder = ArchitectureContextBuilder()

    context = builder.build(
        parsed_modules=[],
        dependency_graph=graph,
    )

    assert context.circular_dependencies == [
        [
            "app.a",
            "app.b",
            "app.c",
            "app.a",
        ]
    ]