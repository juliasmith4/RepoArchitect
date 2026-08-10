from pathlib import Path

from app.analyzer.repository.scanner import RepositoryScanner


def test_ignores_test_files_and_directories(
    tmp_path: Path,
) -> None:
    app_directory = tmp_path / "app"
    tests_directory = tmp_path / "tests"

    app_directory.mkdir()
    tests_directory.mkdir()

    regular_file = app_directory / "service.py"
    test_file = app_directory / "test_service.py"
    test_directory_file = (
        tests_directory / "test_api.py"
    )

    regular_file.write_text(
        "print('service')",
        encoding="utf-8",
    )

    test_file.write_text(
        "print('test')",
        encoding="utf-8",
    )

    test_directory_file.write_text(
        "print('test')",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    files = scanner.scan(tmp_path)

    assert files == [regular_file]
def test_ignores_files_ending_in_test(
    tmp_path: Path,
) -> None:
    regular_file = tmp_path / "service.py"
    test_file = tmp_path / "service_test.py"

    regular_file.write_text("", encoding="utf-8")
    test_file.write_text("", encoding="utf-8")

    scanner = RepositoryScanner()

    files = scanner.scan(tmp_path)

    assert files == [regular_file]