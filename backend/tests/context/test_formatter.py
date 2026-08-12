from app.analyzer.context.formatter import ArchitectureContextFormatter
from app.analyzer.context.models import ArchitectureContext


def test_formats_repository_summary():
    context = ArchitectureContext(
        file_count=5,
        function_count=12,
        class_count=3,
        method_count=8,
    )

    formatter = ArchitectureContextFormatter()

    result = formatter.format(context)

    assert "Repository Summary:" in result
    assert "- Files: 5" in result
    assert "- Functions: 12" in result
    assert "- Classes: 3" in result
    assert "- Methods: 8" in result


def test_formats_modules():
    context = ArchitectureContext(
        modules=[
            "app.main",
            "app.services.users",
        ]
    )

    formatter = ArchitectureContextFormatter()

    result = formatter.format(context)

    assert "Modules:" in result
    assert "- app.main" in result
    assert "- app.services.users" in result


def test_formats_empty_modules():
    context = ArchitectureContext()

    formatter = ArchitectureContextFormatter()

    result = formatter.format(context)

    assert "Modules:" in result
    assert "- None" in result


def test_formats_dependencies():
    context = ArchitectureContext(
        internal_dependencies=[
            "app.main -> app.services.users",
        ],
        external_dependencies=[
            "app.main -> fastapi",
        ],
        unresolved_dependencies=[
            "app.main -> unknown_package",
        ],
    )

    formatter = ArchitectureContextFormatter()

    result = formatter.format(context)

    assert "Dependencies:" in result

    assert "Internal:" in result
    assert "- app.main -> app.services.users" in result

    assert "External:" in result
    assert "- app.main -> fastapi" in result

    assert "Unresolved:" in result
    assert "- app.main -> unknown_package" in result


def test_formats_architectural_findings():
    context = ArchitectureContext(
        most_depended_on_modules=[
            "app.services.users",
        ],
        isolated_modules=[
            "app.unused",
        ],
        circular_dependencies=[
            [
                "app.a",
                "app.b",
                "app.c",
                "app.a",
            ],
        ],
    )

    formatter = ArchitectureContextFormatter()

    result = formatter.format(context)

    assert "Architectural Findings:" in result

    assert "Most depended-on modules:" in result
    assert "- app.services.users" in result

    assert "Isolated modules:" in result
    assert "- app.unused" in result

    assert "Circular dependencies:" in result
    assert "- app.a -> app.b -> app.c -> app.a" in result


def test_formats_complete_architecture_context():
    context = ArchitectureContext(
        file_count=3,
        function_count=7,
        class_count=2,
        method_count=4,
        modules=[
            "app.main",
            "app.services.users",
            "app.database",
        ],
        internal_dependencies=[
            "app.main -> app.services.users",
            "app.services.users -> app.database",
        ],
        external_dependencies=[
            "app.main -> fastapi",
        ],
        unresolved_dependencies=[
            "app.database -> unknown_driver",
        ],
        most_depended_on_modules=[
            "app.services.users",
            "app.database",
        ],
        isolated_modules=[],
        circular_dependencies=[],
    )

    formatter = ArchitectureContextFormatter()

    result = formatter.format(context)

    assert "Repository Summary:" in result
    assert "- Files: 3" in result
    assert "- Functions: 7" in result
    assert "- Classes: 2" in result
    assert "- Methods: 4" in result

    assert "Modules:" in result
    assert "- app.main" in result
    assert "- app.services.users" in result
    assert "- app.database" in result

    assert "Internal:" in result
    assert "- app.main -> app.services.users" in result
    assert "- app.services.users -> app.database" in result

    assert "External:" in result
    assert "- app.main -> fastapi" in result

    assert "Unresolved:" in result
    assert "- app.database -> unknown_driver" in result

    assert "Most depended-on modules:" in result
    assert "- app.services.users" in result
    assert "- app.database" in result