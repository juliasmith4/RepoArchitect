from pathlib import Path

from app.analyzer.graph import (
    DependencyGraphAnalyzer,
    DependencyType,
)
from app.analyzer.service import PythonAnalysisService
from unittest.mock import MagicMock

from app.analyzer.repository.cloner import (
    ClonedRepository,
)

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

    result = service.analyze_repository(
        tmp_path
    )

    assert len(result.modules) == 2

    assert result.graph.has_node("main")
    assert result.graph.has_node(
        "services.users"
    )

    dependencies = result.graph.dependencies_of(
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

    assert result.metrics.module_count == 2

    assert (
        result.metrics.internal_dependency_count
        == 1
    )

    assert (
        result.metrics.external_dependency_count
        == 1
    )

    analyzer = DependencyGraphAnalyzer(
        result.graph
    )

    users_metrics = analyzer.module_metrics(
        "services.users"
    )

    assert (
        users_metrics.incoming_dependencies
        == 1
    )

    assert isinstance(
        result.findings,
        list,
    )
def test_analyzes_repository_url(
    tmp_path: Path,
) -> None:
    repo_path = tmp_path / "repository"
    repo_path.mkdir()

    source_file = repo_path / "main.py"
    source_file.write_text(
        "import requests",
        encoding="utf-8",
    )

    mock_cloner = MagicMock()

    mock_cloner.clone.return_value = (
        ClonedRepository(
            path=repo_path,
            source_url=(
                "https://github.com/example/project"
            ),
        )
    )

    service = PythonAnalysisService(
        cloner=mock_cloner
    )

    result = service.analyze_repository_url(
        "https://github.com/example/project"
    )

    assert result.metrics.module_count == 1

    mock_cloner.clone.assert_called_once_with(
        "https://github.com/example/project"
    )

    mock_cloner.cleanup.assert_called_once_with(
        repo_path.parent
    )