"""Tests for architectural dependency analysis."""

from app.analyzer.dependencies.analyzer import DependencyAnalyzer
from app.analyzer.parsing.models import (
    ParsedCall,
    ParsedFunction,
)


def create_function(
    *,
    name: str = "analyze",
    parent_class: str | None = None,
    calls: list[ParsedCall] | None = None,
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
        assignments=[],
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