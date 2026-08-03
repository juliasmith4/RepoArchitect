"""Tests for the Python analysis service."""

from app.analyzer.service import PythonAnalysisService


def test_analyzes_python_source_end_to_end() -> None:
    source_code = """
from app.parsers import PythonParser


class RepositoryAnalyzer:
    def __init__(self):
        self.parser = PythonParser()

    def analyze(self, path: str):
        return self.parser.parse(path)
"""

    service = PythonAnalysisService()
    result = service.analyze_source(source_code)

    assert len(result.imports) == 1
    assert len(result.functions) == 0
    assert len(result.classes) == 1

    assert result.classes[0].name == "RepositoryAnalyzer"
    assert len(result.classes[0].methods) == 2

    assert [
        dependency.dependency_type
        for dependency in result.dependencies
    ] == [
        "calls",
        "instantiates",
        "calls",
    ]

    assert [
        dependency.target
        for dependency in result.dependencies
    ] == [
        "PythonParser",
        "PythonParser",
        "self.parser.parse",
    ]

    assert (
        result.resolved_dependencies[0].target_category
        == "imported"
    )

    assert (
        result.resolved_dependencies[0].imported_from
        == "app.parsers.PythonParser"
    )

    assert (
        result.resolved_dependencies[1].target_category
        == "imported"
    )

    assert (
        result.resolved_dependencies[2].target_category
        == "unresolved"
    )