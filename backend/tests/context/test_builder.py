from pathlib import Path

from app.analyzer.context import ArchitectureContextBuilder
from app.analyzer.parsing.models import (
    ParsedClass,
    ParsedFunction,
    ParsedModule,
)


def test_builds_architecture_context():
    parsed_modules = [
        ParsedModule(
            path=Path("app/main.py"),
            module_name="app.main",
            functions=[
                ParsedFunction(name="main"),
            ],
            classes=[
                ParsedClass(
                    name="Application",
                    methods=[
                        ParsedFunction(
                            name="run",
                            is_method=True,
                            parent_class="Application",
                        ),
                    ],
                ),
            ],
        ),
        ParsedModule(
            path=Path("app/services/analyzer.py"),
            module_name="app.services.analyzer",
            functions=[
                ParsedFunction(name="analyze"),
                ParsedFunction(name="load_repository"),
            ],
        ),
    ]

    builder = ArchitectureContextBuilder()

    context = builder.build(parsed_modules)

    assert context.file_count == 2
    assert context.function_count == 3
    assert context.class_count == 1
    assert context.method_count == 1
    assert context.modules == [
        "app.main",
        "app.services.analyzer",
    ]


def test_builds_empty_architecture_context():
    builder = ArchitectureContextBuilder()

    context = builder.build([])

    assert context.file_count == 0
    assert context.function_count == 0
    assert context.class_count == 0
    assert context.method_count == 0
    assert context.modules == []


def test_skips_modules_with_parse_errors():
    parsed_modules = [
        ParsedModule(
            path=Path("app/main.py"),
            module_name="app.main",
        ),
        ParsedModule(
            path=Path("app/broken.py"),
            module_name="app.broken",
            parse_error="invalid syntax",
        ),
    ]

    builder = ArchitectureContextBuilder()

    context = builder.build(parsed_modules)

    assert context.file_count == 1
    assert context.function_count == 0
    assert context.class_count == 0
    assert context.method_count == 0
    assert context.modules == [
        "app.main",
    ]