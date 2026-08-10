"""Repository file discovery."""

from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "tests",
    "test",
}


class RepositoryScanner:
    """Find analyzable Python files inside a repository."""

    def scan(
        self,
        repository_path: Path,
    ) -> list[Path]:
        if not repository_path.exists():
            raise ValueError(
                f"Repository does not exist: {repository_path}"
            )

        if not repository_path.is_dir():
            raise ValueError(
                f"Repository path is not a directory: {repository_path}"
            )

        python_files: list[Path] = []

        for file_path in repository_path.rglob("*.py"):
            if self._should_ignore(
                file_path,
                repository_path,
            ):
                continue

            python_files.append(file_path)

        return sorted(python_files)

    @staticmethod
    def _should_ignore(
        file_path: Path,
        repository_path: Path,
    ) -> bool:
        relative_path = file_path.relative_to(
            repository_path
        )

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative_path.parts
        ):
            return True

        if file_path.name.startswith("test_"):
            return True

        if file_path.name.endswith("_test.py"):
            return True

        return False