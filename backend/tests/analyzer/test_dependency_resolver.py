"""Tests for dependency name resolution."""

from app.analyzer.dependencies.models import Dependency
from app.analyzer.dependencies.resolver import DependencyResolver
from app.analyzer.parsing.models import (
    ImportInfo,
    ParsedClass,
    ParsedFunction,
)


def create_function(name: str) -> ParsedFunction:
    """Create a minimal parsed function."""

    return ParsedFunction(
        name=name,
        parameters=[],
        decorators=[],
        return_annotation=None,
        docstring=None,
        start_line=1,
        end_line=2,
        is_async=False,
        is_method=False,
        parent_class=None,
        calls=[],
        assignments=[],
        returns=[],
    )


def create_class(name: str) -> ParsedClass:
    """Create a minimal parsed class."""

    return ParsedClass(
        name=name,
        base_classes=[],
        methods=[],
        decorators=[],
        docstring=None,
        start_line=1,
        end_line=2,
        parent_class=None,
    )


def test_resolves_from_imported_name() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="analyze",
            target="PythonParser",
            dependency_type="calls",
            line_number=4,
        )
    ]

    imports = [
        ImportInfo(
            module="app.analyzer.parsing.parser",
            names=["PythonParser"],
            alias=None,
            line_number=1,
            is_from_import=True,
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=imports,
        functions=[],
        classes=[],
    )

    dependency = resolved[0]

    assert dependency.target_category == "imported"
    assert (
        dependency.imported_from
        == "app.analyzer.parsing.parser.PythonParser"
    )


def test_resolves_aliased_from_import() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="analyze",
            target="Parser",
            dependency_type="calls",
        )
    ]

    imports = [
        ImportInfo(
            module="app.analyzer.parsing.parser",
            names=["PythonParser"],
            alias="Parser",
            line_number=1,
            is_from_import=True,
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=imports,
        functions=[],
        classes=[],
    )

    assert resolved[0].target_category == "imported"
    assert (
        resolved[0].imported_from
        == "app.analyzer.parsing.parser.PythonParser"
    )


def test_resolves_regular_import() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="fetch_repository",
            target="requests.get",
            dependency_type="calls",
        )
    ]

    imports = [
        ImportInfo(
            module="requests",
            names=[],
            alias=None,
            line_number=1,
            is_from_import=False,
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=imports,
        functions=[],
        classes=[],
    )

    assert resolved[0].target_category == "imported"
    assert resolved[0].imported_from == "requests"


def test_resolves_aliased_regular_import() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="build_frame",
            target="pd.DataFrame",
            dependency_type="calls",
        )
    ]

    imports = [
        ImportInfo(
            module="pandas",
            names=[],
            alias="pd",
            line_number=1,
            is_from_import=False,
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=imports,
        functions=[],
        classes=[],
    )

    assert resolved[0].target_category == "imported"
    assert resolved[0].imported_from == "pandas"


def test_resolves_local_function() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="analyze",
            target="normalize_path",
            dependency_type="calls",
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=[],
        functions=[create_function("normalize_path")],
        classes=[],
    )

    assert resolved[0].target_category == "local"
    assert resolved[0].imported_from is None


def test_resolves_local_class() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="build",
            target="RepositoryAnalyzer",
            dependency_type="instantiates",
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=[],
        functions=[],
        classes=[create_class("RepositoryAnalyzer")],
    )

    assert resolved[0].target_category == "local"
    assert resolved[0].imported_from is None


def test_marks_unknown_target_as_unresolved() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="analyze",
            target="unknown_service.process",
            dependency_type="calls",
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=[],
        functions=[],
        classes=[],
    )

    assert resolved[0].target_category == "unresolved"
    assert resolved[0].imported_from is None


def test_preserves_dependency_information() -> None:
    resolver = DependencyResolver()

    dependencies = [
        Dependency(
            source="RepositoryAnalyzer.analyze",
            target="requests.get",
            dependency_type="calls",
            line_number=12,
        )
    ]

    imports = [
        ImportInfo(
            module="requests",
            names=[],
            alias=None,
            line_number=1,
            is_from_import=False,
        )
    ]

    resolved = resolver.resolve_dependencies(
        dependencies=dependencies,
        imports=imports,
        functions=[],
        classes=[],
    )

    dependency = resolved[0]

    assert dependency.source == "RepositoryAnalyzer.analyze"
    assert dependency.target == "requests.get"
    assert dependency.dependency_type == "calls"
    assert dependency.line_number == 12