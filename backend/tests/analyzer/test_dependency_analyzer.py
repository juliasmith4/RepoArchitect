"""Tests for architectural dependency analysis."""

from app.analyzer.dependencies.analyzer import DependencyAnalyzer
from app.analyzer.parsing.models import (
    ParsedAssignment,
    ParsedCall,
    ParsedFunction,
)


def create_function(
    *,
    name: str = "analyze",
    parent_class: str | None = None,
    calls: list[ParsedCall] | None = None,
    assignments: list[ParsedAssignment] | None = None,
) -> ParsedFunction:
    """Create a parsed function for dependency tests."""

    return ParsedFunction(
        name=name,
        parameters=[],
        decorators=[],
        return_annotation=None,
        docstring=None,
        start_line=1,
        end_line=3,
        is_async=False,
        is_method=parent_class is not None,
        parent_class=parent_class,
        calls=calls or [],
        assignments=assignments or [],
        returns=[],
    )


def test_analyzes_direct_function_call() -> None:
    function = create_function(
        calls=[
            ParsedCall(
                name="parse_repository",
                line_number=2,
            )
        ]
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(function)

    assert len(dependencies) == 1

    dependency = dependencies[0]

    assert dependency.source == "analyze"
    assert dependency.target == "parse_repository"
    assert dependency.dependency_type == "calls"
    assert dependency.line_number == 2


def test_uses_qualified_name_for_method() -> None:
    method = create_function(
        name="analyze",
        parent_class="RepositoryAnalyzer",
        calls=[
            ParsedCall(
                name="self.parser.parse",
                line_number=4,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(method)

    dependency = dependencies[0]

    assert dependency.source == "RepositoryAnalyzer.analyze"
    assert dependency.target == "self.parser.parse"


def test_analyzes_multiple_calls() -> None:
    function = create_function(
        calls=[
            ParsedCall(
                name="load_repository",
                line_number=2,
            ),
            ParsedCall(
                name="validate_repository",
                line_number=3,
            ),
        ]
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(function)

    assert [dependency.target for dependency in dependencies] == [
        "load_repository",
        "validate_repository",
    ]


def test_function_without_calls_has_no_dependencies() -> None:
    function = create_function()

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(function)

    assert dependencies == []


def test_detects_constructor_instantiation() -> None:
    constructor = create_function(
        name="__init__",
        parent_class="RepositoryAnalyzer",
        assignments=[
            ParsedAssignment(
                target="self.parser",
                value="PythonParser()",
                line_number=3,
                is_instance_attribute=True,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(constructor)

    instantiations = [
        dependency
        for dependency in dependencies
        if dependency.dependency_type == "instantiates"
    ]

    assert len(instantiations) == 1

    dependency = instantiations[0]

    assert dependency.source == "RepositoryAnalyzer"
    assert dependency.target == "PythonParser"
    assert dependency.line_number == 3


def test_detects_multiple_constructor_instantiations() -> None:
    constructor = create_function(
        name="__init__",
        parent_class="RepositoryAnalyzer",
        assignments=[
            ParsedAssignment(
                target="self.parser",
                value="PythonParser()",
                line_number=3,
                is_instance_attribute=True,
            ),
            ParsedAssignment(
                target="self.database",
                value="DatabaseClient()",
                line_number=4,
                is_instance_attribute=True,
            ),
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(constructor)

    instantiations = [
        dependency
        for dependency in dependencies
        if dependency.dependency_type == "instantiates"
    ]

    assert [dependency.target for dependency in instantiations] == [
        "PythonParser",
        "DatabaseClient",
    ]


def test_detects_qualified_constructor_name() -> None:
    constructor = create_function(
        name="__init__",
        parent_class="RepositoryAnalyzer",
        assignments=[
            ParsedAssignment(
                target="self.client",
                value="services.clients.RepositoryClient()",
                line_number=3,
                is_instance_attribute=True,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(constructor)

    instantiation = next(
        dependency
        for dependency in dependencies
        if dependency.dependency_type == "instantiates"
    )

    assert (
        instantiation.target
        == "services.clients.RepositoryClient"
    )


def test_does_not_classify_parameter_assignment_as_instantiation() -> None:
    constructor = create_function(
        name="__init__",
        parent_class="RepositoryAnalyzer",
        assignments=[
            ParsedAssignment(
                target="self.parser",
                value="parser",
                line_number=3,
                is_instance_attribute=True,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(constructor)

    assert all(
        dependency.dependency_type != "instantiates"
        for dependency in dependencies
    )


def test_does_not_classify_local_assignment_as_instantiation() -> None:
    constructor = create_function(
        name="__init__",
        parent_class="RepositoryAnalyzer",
        assignments=[
            ParsedAssignment(
                target="parser",
                value="PythonParser()",
                line_number=3,
                is_instance_attribute=False,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(constructor)

    assert all(
        dependency.dependency_type != "instantiates"
        for dependency in dependencies
    )


def test_does_not_classify_non_constructor_assignment() -> None:
    function = create_function(
        name="analyze",
        parent_class="RepositoryAnalyzer",
        assignments=[
            ParsedAssignment(
                target="self.parser",
                value="PythonParser()",
                line_number=3,
                is_instance_attribute=True,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(function)

    assert all(
        dependency.dependency_type != "instantiates"
        for dependency in dependencies
    )


def test_preserves_call_and_instantiation_dependencies() -> None:
    constructor = create_function(
        name="__init__",
        parent_class="RepositoryAnalyzer",
        calls=[
            ParsedCall(
                name="PythonParser",
                line_number=3,
            )
        ],
        assignments=[
            ParsedAssignment(
                target="self.parser",
                value="PythonParser()",
                line_number=3,
                is_instance_attribute=True,
            )
        ],
    )

    analyzer = DependencyAnalyzer()
    dependencies = analyzer.analyze_function(constructor)

    assert [
        (
            dependency.source,
            dependency.target,
            dependency.dependency_type,
        )
        for dependency in dependencies
    ] == [
        (
            "RepositoryAnalyzer.__init__",
            "PythonParser",
            "calls",
        ),
        (
            "RepositoryAnalyzer",
            "PythonParser",
            "instantiates",
        ),
    ]

def load():
    read_file()

class RepositoryAnalyzer:
    def __init__(self):
        self.parser = PythonParser()

    def analyze(self):
        self.parser.parse()