"""Clone remote Git repositories for analysis."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(slots=True)
class ClonedRepository:
    """Information about a temporarily cloned repository."""

    path: Path
    source_url: str


class RepositoryCloner:
    """Clone public Git repositories into a temporary directory."""

    def clone(
        self,
        repository_url: str,
    ) -> ClonedRepository:
        self._validate_repository_url(repository_url)

        temp_directory = Path(
            tempfile.mkdtemp(
                prefix="repoarchitect-"
            )
        )

        repository_directory = (
            temp_directory / "repository"
        )

        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    repository_url,
                    str(repository_directory),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            self.cleanup(temp_directory)

            raise RuntimeError(
                "Git is not installed or is not available "
                "on the system PATH."
            ) from error

        except subprocess.CalledProcessError as error:
            self.cleanup(temp_directory)

            message = (
                error.stderr.strip()
                or error.stdout.strip()
                or "Unknown git clone error."
            )

            raise ValueError(
                f"Unable to clone repository: {message}"
            ) from error

        return ClonedRepository(
            path=repository_directory,
            source_url=repository_url,
        )

    @staticmethod
    def cleanup(
        repository_path: Path,
    ) -> None:
        """
        Remove a cloned repository or its temporary parent directory.
        """

        path = repository_path.resolve()

        if not path.exists():
            return

        shutil.rmtree(
            path,
            ignore_errors=True,
        )

    @staticmethod
    def _validate_repository_url(
        repository_url: str,
    ) -> None:
        """Validate that the repository URL is a supported HTTPS URL."""

        parsed_url = urlparse(repository_url)

        if parsed_url.scheme != "https":
            raise ValueError(
                "Repository URL must use HTTPS."
            )

        if not parsed_url.netloc:
            raise ValueError(
                "Repository URL must contain a valid host."
            )

        if parsed_url.hostname not in {
            "github.com",
            "www.github.com",
        }:
            raise ValueError(
                "Only public GitHub repository URLs "
                "are currently supported."
            )

        path_parts = [
            part
            for part in parsed_url.path.split("/")
            if part
        ]

        if len(path_parts) < 2:
            raise ValueError(
                "Repository URL must include an owner "
                "and repository name."
            )