from pathlib import Path

import pytest

from app.analyzer.parsing.models import (
    ImportInfo,
    ParsedClass,
    ParsedFile,
    ParsedFunction,
    ParsedParameter,
)


@pytest.mark.parametrize(
    ("start_line", "end_line", "expected"),
    [
        (1, 1, 1),
        (1, 10, 10),
        (10, 19, 10),
        (100, 150, 51),
        (None, 10, None),
        (10, None, None),
        (None, None, None),
    ],
)
def test_parsed_function_line_count(
    start_line: int | None,
    end_line: int | None,
    expected: int | None,
) -> None:
    parsed_function = ParsedFunction(
        name="analyze_repository",
        start_line=start_line,
        end_line=end_line,
    )

    assert parsed_function.line_count == expected


@pytest.mark.parametrize(
    ("start_line", "end_line", "expected"),
    [
        (1, 1, 1),
        (5, 24, 20),
        (50, 99, 50),
        (None, 20, None),
        (5, None, None),
        (None, None, None),
    ],
)
def test_parsed_class_line_count(
    start_line: int | None,
    end_line: int | None,
    expected: int | None,
) -> None:
    parsed_class = ParsedClass(
        name="RepositoryAnalyzer",
        start_line=start_line,
        end_line=end_line,
    )

    assert parsed_class.line_count == expected


def test_empty_parsed_file_has_zero_counts() -> None:
    parsed_file = ParsedFile(
        path=Path("empty.py"),
        module_name="empty",
    )

    assert parsed_file.function_count == 0
    assert parsed_file.class_count == 0
    assert parsed_file.method_count == 0
    assert parsed_file.imports == []
    assert parsed_file.functions == []
    assert parsed_file.classes == []


def test_parsed_file_counts() -> None:
    parsed_file = ParsedFile(
        path=Path("app/example.py"),
        module_name="app.example",
        functions=[
            ParsedFunction(name="first_function"),
            ParsedFunction(name="second_function"),
        ],
        classes=[
            ParsedClass(
                name="FirstClass",
                methods=[
                    ParsedFunction(
                        name="first_method",
                        is_method=True,
                        parent_class="FirstClass",
                    ),
                    ParsedFunction(
                        name="second_method",
                        is_method=True,
                        parent_class="FirstClass",
                    ),
                ],
            ),
            ParsedClass(
                name="SecondClass",
                methods=[
                    ParsedFunction(
                        name="third_method",
                        is_method=True,
                        parent_class="SecondClass",
                    ),
                ],
            ),
        ],
    )

    assert parsed_file.function_count == 2
    assert parsed_file.class_count == 2
    assert parsed_file.method_count == 3


def test_methods_are_not_counted_as_top_level_functions() -> None:
    parsed_file = ParsedFile(
        path=Path("analyzer.py"),
        module_name="analyzer",
        classes=[
            ParsedClass(
                name="Analyzer",
                methods=[
                    ParsedFunction(
                        name="run",
                        is_method=True,
                        parent_class="Analyzer",
                    ),
                    ParsedFunction(
                        name="validate",
                        is_method=True,
                        parent_class="Analyzer",
                    ),
                ],
            )
        ],
    )

    assert parsed_file.function_count == 0
    assert parsed_file.class_count == 1
    assert parsed_file.method_count == 2


def test_classes_without_methods_have_zero_method_count() -> None:
    parsed_file = ParsedFile(
        path=Path("models.py"),
        module_name="models",
        classes=[
            ParsedClass(name="Repository"),
            ParsedClass(name="Analysis"),
            ParsedClass(name="Finding"),
        ],
    )

    assert parsed_file.class_count == 3
    assert parsed_file.method_count == 0


def test_parsed_file_was_parsed_successfully() -> None:
    parsed_file = ParsedFile(
        path=Path("app/example.py"),
        module_name="app.example",
    )

    assert parsed_file.was_parsed_successfully is True


def test_parsed_file_was_not_parsed_successfully() -> None:
    parsed_file = ParsedFile(
        path=Path("app/broken.py"),
        module_name="app.broken",
        parse_error="Invalid Python syntax",
    )

    assert parsed_file.was_parsed_successfully is False
    assert parsed_file.parse_error == "Invalid Python syntax"


def test_parsed_function_stores_metadata() -> None:
    parsed_function = ParsedFunction(
        name="analyze_repository",
        parameters=[
            ParsedParameter(
                name="repository_url",
                annotation="str",
            ),
            ParsedParameter(
                name="recursive",
                annotation="bool",
                default_value="True",
            ),
        ],
        decorators=["staticmethod", "retry"],
        return_annotation="AnalysisResult",
        docstring="Analyze a repository.",
        start_line=12,
        end_line=36,
        is_async=True,
        is_method=True,
        parent_class="RepositoryAnalyzer",
    )

    assert parsed_function.name == "analyze_repository"
    assert len(parsed_function.parameters) == 2
    assert parsed_function.parameters[0].name == "repository_url"
    assert parsed_function.parameters[0].annotation == "str"
    assert parsed_function.parameters[1].default_value == "True"
    assert parsed_function.decorators == ["staticmethod", "retry"]
    assert parsed_function.return_annotation == "AnalysisResult"
    assert parsed_function.docstring == "Analyze a repository."
    assert parsed_function.is_async is True
    assert parsed_function.is_method is True
    assert parsed_function.parent_class == "RepositoryAnalyzer"
    assert parsed_function.line_count == 25


def test_parsed_class_stores_metadata() -> None:
    parsed_class = ParsedClass(
        name="RepositoryAnalyzer",
        base_classes=["BaseAnalyzer", "LoggingMixin"],
        methods=[
            ParsedFunction(
                name="analyze",
                is_method=True,
                parent_class="RepositoryAnalyzer",
            )
        ],
        decorators=["dataclass"],
        docstring="Analyzes Python repositories.",
        start_line=10,
        end_line=75,
    )

    assert parsed_class.name == "RepositoryAnalyzer"
    assert parsed_class.base_classes == [
        "BaseAnalyzer",
        "LoggingMixin",
    ]
    assert len(parsed_class.methods) == 1
    assert parsed_class.decorators == ["dataclass"]
    assert parsed_class.docstring == "Analyzes Python repositories."
    assert parsed_class.line_count == 66


def test_import_info_stores_regular_import() -> None:
    import_info = ImportInfo(
        module="pandas",
        alias="pd",
        line_number=3,
        is_from_import=False,
    )

    assert import_info.module == "pandas"
    assert import_info.names == []
    assert import_info.alias == "pd"
    assert import_info.line_number == 3
    assert import_info.is_from_import is False


def test_import_info_stores_from_import() -> None:
    import_info = ImportInfo(
        module="pathlib",
        names=["Path", "PurePath"],
        line_number=2,
        is_from_import=True,
    )

    assert import_info.module == "pathlib"
    assert import_info.names == ["Path", "PurePath"]
    assert import_info.alias is None
    assert import_info.line_number == 2
    assert import_info.is_from_import is True


def test_parsed_file_default_lists_are_independent() -> None:
    first_file = ParsedFile(
        path=Path("first.py"),
        module_name="first",
    )
    second_file = ParsedFile(
        path=Path("second.py"),
        module_name="second",
    )

    first_file.imports.append(ImportInfo(module="os"))
    first_file.functions.append(ParsedFunction(name="main"))
    first_file.classes.append(ParsedClass(name="Analyzer"))

    assert len(first_file.imports) == 1
    assert len(first_file.functions) == 1
    assert len(first_file.classes) == 1

    assert second_file.imports == []
    assert second_file.functions == []
    assert second_file.classes == []


def test_parsed_function_default_lists_are_independent() -> None:
    first_function = ParsedFunction(name="first")
    second_function = ParsedFunction(name="second")

    first_function.parameters.append(
        ParsedParameter(
            name="repository_url",
            annotation="str",
        )
    )
    first_function.decorators.append("staticmethod")

    assert len(first_function.parameters) == 1
    assert first_function.decorators == ["staticmethod"]

    assert second_function.parameters == []
    assert second_function.decorators == []


def test_parsed_class_default_lists_are_independent() -> None:
    first_class = ParsedClass(name="FirstClass")
    second_class = ParsedClass(name="SecondClass")

    first_class.base_classes.append("BaseAnalyzer")
    first_class.methods.append(
        ParsedFunction(
            name="analyze",
            is_method=True,
            parent_class="FirstClass",
        )
    )
    first_class.decorators.append("dataclass")

    assert first_class.base_classes == ["BaseAnalyzer"]
    assert len(first_class.methods) == 1
    assert first_class.decorators == ["dataclass"]

    assert second_class.base_classes == []
    assert second_class.methods == []
    assert second_class.decorators == []


def test_slots_prevent_undefined_attributes() -> None:
    parsed_function = ParsedFunction(name="analyze")

    with pytest.raises(AttributeError):
        setattr(parsed_function, "unexpected_attribute", "value")