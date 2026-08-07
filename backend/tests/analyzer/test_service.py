from pathlib import Path

from app.analyzer.graph import DependencyType
from app.analyzer.service import PythonAnalysisService


def test_analyzes_repository_end_to_end(
    tmp_path: Path,
) -> None:
    services_directory = (
        tmp_path / "services"
    )

    services_directory.mkdir()

    main_file = tmp_path / "main.py"
    users_file = (
        services_directory / "users.py"
    )

    main_file.write_text(
        """
from services.users import get_user
import requests


def run():
    return get_user()
""".strip(),
        encoding="utf-8",
    )

    users_file.write_text(
        """
def get_user():
    return {"id": 1}
""".strip(),
        encoding="utf-8",
    )

    service = PythonAnalysisService()

    modules, graph, analyzer = (
        service.analyze_repository(tmp_path)
    )

    assert len(modules) == 2

    assert graph.has_node("main")
    assert graph.has_node(
        "services.users"
    )

    dependencies = graph.dependencies_of(
        "main"
    )

    internal_dependency = next(
        edge
        for edge in dependencies
        if edge.target == "services.users"
    )

    external_dependency = next(
        edge
        for edge in dependencies
        if edge.target == "requests"
    )

    assert (
        internal_dependency.dependency_type
        == DependencyType.INTERNAL
    )

    assert (
        external_dependency.dependency_type
        == DependencyType.EXTERNAL
    )

    users_metrics = analyzer.module_metrics(
        "services.users"
    )

    assert (
        users_metrics.incoming_dependencies
        == 1
    )