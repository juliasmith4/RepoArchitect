from pathlib import Path
from unittest.mock import patch

import pytest

from app.analyzer.repository.cloner import RepositoryCloner


def test_rejects_non_https_url() -> None:
    cloner = RepositoryCloner()

    with pytest.raises(ValueError):
        cloner.clone(
            "http://github.com/example/project"
        )


def test_rejects_non_github_url() -> None:
    cloner = RepositoryCloner()

    with pytest.raises(ValueError):
        cloner.clone(
            "https://gitlab.com/example/project"
        )


def test_rejects_url_without_repository_name() -> None:
    cloner = RepositoryCloner()

    with pytest.raises(ValueError):
        cloner.clone(
            "https://github.com/example"
        )


@patch("app.analyzer.repository.cloner.subprocess.run")
def test_clones_public_github_repository(
    mock_run,
) -> None:
    cloner = RepositoryCloner()

    result = cloner.clone(
        "https://github.com/example/project"
    )

    mock_run.assert_called_once()

    command = mock_run.call_args.args[0]

    assert command[0] == "git"
    assert command[1] == "clone"
    assert "--depth" in command
    assert "1" in command

    assert result.source_url == (
        "https://github.com/example/project"
    )

    cloner.cleanup(
        result.path.parent
    )


def test_cleanup_removes_directory(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "repo"
    directory.mkdir()

    assert directory.exists()

    RepositoryCloner.cleanup(directory)

    assert not directory.exists()