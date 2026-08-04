from pathlib import Path

from app.analyzer.graph import (
    DependencyGraphBuilder,
    DependencyType,
)
from app.analyzer.graph.builder import resolve_relative_import
from app.analyzer.parsing.models import (
    ImportInfo,
    ParsedModule,
)


def test_resolves_same_package_import() -> None:
    result = resolve_relative_import(
        source_module="app.analyzer.parsing.python_parser",
        imported_module=".models",
    )

    assert result == "app.analyzer.parsing.models"


def test_resolves_parent_package_import() -> None:
    result = resolve_relative_import(
        source_module="app.analyzer.parsing.python_parser",
        imported_module="..graph",
    )

    assert result == "app.analyzer.graph"