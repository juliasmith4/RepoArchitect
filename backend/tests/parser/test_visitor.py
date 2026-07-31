import ast

from app.analyzer.parsing.visitor import (
    PythonAstVisitor,
    expression_to_string,
    parse_parameters,
)


def create_visitor(source: str) -> PythonAstVisitor:
    visitor = PythonAstVisitor()
    visitor.visit(ast.parse(source))
    return visitor


def test_collects_complete_module_structure() -> None:
    source = '''
import os
import pandas as pd
from pathlib import Path
from typing import Any as Anything


class Analyzer:
    """Analyze a repository."""

    def run(self, path: Path, *, strict: bool = False) -> bool:
        """Run the analyzer."""
        return True


async def main(name: str = "RepoArchitect") -> None:
    pass
'''

    visitor = create_visitor(source)

    assert len(visitor.imports) == 4
    assert len(visitor.functions) == 1
    assert len(visitor.classes) == 1

    main = visitor.functions[0]

    assert main.name == "main"
    assert main.is_async is True
    assert main.is_method is False
    assert main.parent_class is None
    assert main.return_annotation == "None"
    assert len(main.parameters) == 1
    assert main.parameters[0].name == "name"
    assert main.parameters[0].annotation == "str"
    assert main.parameters[0].default_value == "'RepoArchitect'"

    analyzer = visitor.classes[0]

    assert analyzer.name == "Analyzer"
    assert analyzer.docstring == "Analyze a repository."
    assert analyzer.parent_class is None
    assert len(analyzer.methods) == 1

    run = analyzer.methods[0]

    assert run.name == "run"
    assert run.is_async is False
    assert run.is_method is True
    assert run.parent_class == "Analyzer"
    assert run.docstring == "Run the analyzer."
    assert run.return_annotation == "bool"


def test_collects_regular_import() -> None:
    visitor = create_visitor("import os")

    assert len(visitor.imports) == 1

    imported = visitor.imports[0]

    assert imported.module == "os"
    assert imported.names == []
    assert imported.alias is None
    assert imported.is_from_import is False
    assert imported.line_number == 1


def test_collects_aliased_import() -> None:
    visitor = create_visitor("import pandas as pd")

    assert len(visitor.imports) == 1

    imported = visitor.imports[0]

    assert imported.module == "pandas"
    assert imported.names == []
    assert imported.alias == "pd"
    assert imported.is_from_import is False


def test_collects_multiple_regular_imports_from_one_statement() -> None:
    visitor = create_visitor("import os, sys as system")

    assert len(visitor.imports) == 2

    first_import = visitor.imports[0]
    second_import = visitor.imports[1]

    assert first_import.module == "os"
    assert first_import.alias is None

    assert second_import.module == "sys"
    assert second_import.alias == "system"


def test_collects_from_import() -> None:
    visitor = create_visitor("from pathlib import Path")

    assert len(visitor.imports) == 1

    imported = visitor.imports[0]

    assert imported.module == "pathlib"
    assert imported.names == ["Path"]
    assert imported.alias is None
    assert imported.is_from_import is True
    assert imported.line_number == 1


def test_collects_aliased_from_import() -> None:
    visitor = create_visitor("from typing import Any as Anything")

    assert len(visitor.imports) == 1

    imported = visitor.imports[0]

    assert imported.module == "typing"
    assert imported.names == ["Any"]
    assert imported.alias == "Anything"
    assert imported.is_from_import is True


def test_collects_multiple_names_from_import_statement() -> None:
    visitor = create_visitor(
        "from pathlib import Path, PurePath as BasePath"
    )

    assert len(visitor.imports) == 2

    first_import = visitor.imports[0]
    second_import = visitor.imports[1]

    assert first_import.module == "pathlib"
    assert first_import.names == ["Path"]
    assert first_import.alias is None

    assert second_import.module == "pathlib"
    assert second_import.names == ["PurePath"]
    assert second_import.alias == "BasePath"


def test_collects_relative_import() -> None:
    visitor = create_visitor("from . import models")

    assert len(visitor.imports) == 1

    imported = visitor.imports[0]

    assert imported.module == ""
    assert imported.names == ["models"]
    assert imported.is_from_import is True


def test_collects_top_level_function() -> None:
    visitor = create_visitor(
        """
def greet(name: str = "World") -> str:
    return f"Hello {name}"
"""
    )

    assert len(visitor.functions) == 1

    function = visitor.functions[0]

    assert function.name == "greet"
    assert function.return_annotation == "str"
    assert function.is_async is False
    assert function.is_method is False
    assert function.parent_class is None


def test_collects_async_function() -> None:
    visitor = create_visitor(
        """
async def main() -> None:
    pass
"""
    )

    assert len(visitor.functions) == 1

    function = visitor.functions[0]

    assert function.name == "main"
    assert function.is_async is True
    assert function.is_method is False
    assert function.return_annotation == "None"


def test_collects_function_parameters() -> None:
    visitor = create_visitor(
        """
def configure(
    name: str,
    count: int = 3,
    enabled: bool = True,
) -> None:
    pass
"""
    )

    function = visitor.functions[0]

    assert len(function.parameters) == 3

    name_parameter = function.parameters[0]
    count_parameter = function.parameters[1]
    enabled_parameter = function.parameters[2]

    assert name_parameter.name == "name"
    assert name_parameter.annotation == "str"
    assert name_parameter.default_value is None

    assert count_parameter.name == "count"
    assert count_parameter.annotation == "int"
    assert count_parameter.default_value == "3"

    assert enabled_parameter.name == "enabled"
    assert enabled_parameter.annotation == "bool"
    assert enabled_parameter.default_value == "True"


def test_collects_positional_only_parameters() -> None:
    visitor = create_visitor(
        """
def divide(
    numerator: float,
    denominator: float,
    /,
) -> float:
    return numerator / denominator
"""
    )

    function = visitor.functions[0]

    assert [parameter.name for parameter in function.parameters] == [
        "numerator",
        "denominator",
    ]

    assert function.parameters[0].annotation == "float"
    assert function.parameters[1].annotation == "float"


def test_collects_varargs_and_kwargs() -> None:
    visitor = create_visitor(
        """
def collect(
    first: str,
    *items: int,
    **options: bool,
) -> None:
    pass
"""
    )

    function = visitor.functions[0]

    assert [parameter.name for parameter in function.parameters] == [
        "first",
        "*items",
        "**options",
    ]

    assert function.parameters[0].annotation == "str"
    assert function.parameters[1].annotation == "int"
    assert function.parameters[2].annotation == "bool"


def test_collects_keyword_only_parameter() -> None:
    visitor = create_visitor(
        """
def run(*, strict: bool = False) -> None:
    pass
"""
    )

    function = visitor.functions[0]

    assert len(function.parameters) == 1

    parameter = function.parameters[0]

    assert parameter.name == "strict"
    assert parameter.annotation == "bool"
    assert parameter.default_value == "False"


def test_collects_required_keyword_only_parameter() -> None:
    visitor = create_visitor(
        """
def run(*, config: dict[str, str]) -> None:
    pass
"""
    )

    function = visitor.functions[0]
    parameter = function.parameters[0]

    assert parameter.name == "config"
    assert parameter.annotation == "dict[str, str]"
    assert parameter.default_value is None


def test_collects_function_decorators() -> None:
    visitor = create_visitor(
        """
@staticmethod
@custom.decorator("value")
def analyze() -> None:
    pass
"""
    )

    function = visitor.functions[0]

    assert function.decorators == [
        "staticmethod",
        "custom.decorator('value')",
    ]


def test_collects_class_decorators() -> None:
    visitor = create_visitor(
        """
@dataclass(slots=True)
class Result:
    pass
"""
    )

    parsed_class = visitor.classes[0]

    assert parsed_class.decorators == ["dataclass(slots=True)"]


def test_collects_base_classes() -> None:
    visitor = create_visitor(
        """
class Analyzer(BaseAnalyzer, LoggingMixin):
    pass
"""
    )

    parsed_class = visitor.classes[0]

    assert parsed_class.base_classes == [
        "BaseAnalyzer",
        "LoggingMixin",
    ]


def test_collects_generic_base_class() -> None:
    visitor = create_visitor(
        """
class RepositoryService(Generic[T]):
    pass
"""
    )

    parsed_class = visitor.classes[0]

    assert parsed_class.base_classes == ["Generic[T]"]


def test_collects_function_docstring() -> None:
    visitor = create_visitor(
        '''
def analyze() -> None:
    """Analyze a repository."""
    pass
'''
    )

    function = visitor.functions[0]

    assert function.docstring == "Analyze a repository."


def test_function_without_docstring_has_none() -> None:
    visitor = create_visitor(
        """
def analyze() -> None:
    pass
"""
    )

    assert visitor.functions[0].docstring is None


def test_collects_class_docstring() -> None:
    visitor = create_visitor(
        '''
class Analyzer:
    """Analyze Python repositories."""
'''
    )

    assert (
        visitor.classes[0].docstring
        == "Analyze Python repositories."
    )


def test_class_without_docstring_has_none() -> None:
    visitor = create_visitor(
        """
class Analyzer:
    pass
"""
    )

    assert visitor.classes[0].docstring is None


def test_method_is_not_added_to_top_level_functions() -> None:
    visitor = create_visitor(
        """
class Analyzer:
    def run(self) -> None:
        pass
"""
    )

    assert visitor.functions == []
    assert len(visitor.classes) == 1
    assert len(visitor.classes[0].methods) == 1


def test_method_stores_parent_class() -> None:
    visitor = create_visitor(
        """
class Analyzer:
    def run(self) -> None:
        pass
"""
    )

    method = visitor.classes[0].methods[0]

    assert method.name == "run"
    assert method.is_method is True
    assert method.parent_class == "Analyzer"


def test_async_method_is_stored_inside_class() -> None:
    visitor = create_visitor(
        """
class Analyzer:
    async def run(self) -> None:
        pass
"""
    )

    method = visitor.classes[0].methods[0]

    assert method.name == "run"
    assert method.is_async is True
    assert method.is_method is True
    assert method.parent_class == "Analyzer"


def test_collects_multiple_methods_in_source_order() -> None:
    visitor = create_visitor(
        """
class Analyzer:
    def parse(self) -> None:
        pass

    def calculate(self) -> None:
        pass

    async def summarize(self) -> None:
        pass
"""
    )

    methods = visitor.classes[0].methods

    assert [method.name for method in methods] == [
        "parse",
        "calculate",
        "summarize",
    ]


def test_collects_multiple_top_level_functions_in_source_order() -> None:
    visitor = create_visitor(
        """
def first() -> None:
    pass


def second() -> None:
    pass


async def third() -> None:
    pass
"""
    )

    assert [function.name for function in visitor.functions] == [
        "first",
        "second",
        "third",
    ]


def test_nested_function_is_not_collected_as_top_level() -> None:
    visitor = create_visitor(
        """
def outer() -> None:
    def inner() -> None:
        pass

    inner()
"""
    )

    assert len(visitor.functions) == 1
    assert visitor.functions[0].name == "outer"


def test_class_declared_inside_function_is_ignored() -> None:
    visitor = create_visitor(
        """
def factory() -> None:
    class LocalAnalyzer:
        pass
"""
    )

    assert len(visitor.functions) == 1
    assert visitor.functions[0].name == "factory"
    assert visitor.classes == []


def test_collects_nested_class_parent_relationship() -> None:
    visitor = create_visitor(
        """
class Outer:
    class Inner:
        pass
"""
    )

    assert len(visitor.classes) == 2

    outer = visitor.classes[0]
    inner = visitor.classes[1]

    assert outer.name == "Outer"
    assert outer.parent_class is None

    assert inner.name == "Inner"
    assert inner.parent_class == "Outer"


def test_nested_class_method_uses_nested_class_as_parent() -> None:
    visitor = create_visitor(
        """
class Outer:
    class Inner:
        def run(self) -> None:
            pass
"""
    )

    inner = visitor.classes[1]
    method = inner.methods[0]

    assert inner.name == "Inner"
    assert inner.parent_class == "Outer"
    assert method.name == "run"
    assert method.parent_class == "Inner"
    assert method.is_method is True


def test_collects_function_line_numbers() -> None:
    visitor = create_visitor(
        """
def first() -> None:
    value = 1
    return None
"""
    )

    function = visitor.functions[0]

    assert function.start_line == 2
    assert function.end_line == 4
    assert function.line_count == 3


def test_collects_class_line_numbers() -> None:
    visitor = create_visitor(
        """
class Analyzer:
    def run(self) -> None:
        pass
"""
    )

    parsed_class = visitor.classes[0]

    assert parsed_class.start_line == 2
    assert parsed_class.end_line == 4
    assert parsed_class.line_count == 3


def test_expression_to_string_returns_none_for_none() -> None:
    assert expression_to_string(None) is None


def test_expression_to_string_handles_simple_annotation() -> None:
    expression = ast.parse("str", mode="eval").body

    assert expression_to_string(expression) == "str"


def test_expression_to_string_handles_complex_annotation() -> None:
    expression = ast.parse(
        "list[dict[str, int]] | None",
        mode="eval",
    ).body

    assert (
        expression_to_string(expression)
        == "list[dict[str, int]] | None"
    )


def test_expression_to_string_handles_default_collection() -> None:
    expression = ast.parse(
        '{"enabled": True}',
        mode="eval",
    ).body

    assert expression_to_string(expression) == "{'enabled': True}"


def test_parse_parameters_handles_empty_arguments() -> None:
    module = ast.parse(
        """
def example():
    pass
"""
    )

    function_node = module.body[0]

    assert isinstance(function_node, ast.FunctionDef)

    parameters = parse_parameters(function_node.args)

    assert parameters == []


def test_parse_parameters_matches_defaults_to_final_arguments() -> None:
    module = ast.parse(
        """
def example(first, second, third=3, fourth=4):
    pass
"""
    )

    function_node = module.body[0]

    assert isinstance(function_node, ast.FunctionDef)

    parameters = parse_parameters(function_node.args)

    assert parameters[0].name == "first"
    assert parameters[0].default_value is None

    assert parameters[1].name == "second"
    assert parameters[1].default_value is None

    assert parameters[2].name == "third"
    assert parameters[2].default_value == "3"

    assert parameters[3].name == "fourth"
    assert parameters[3].default_value == "4"


def test_visitor_starts_with_empty_collections() -> None:
    visitor = PythonAstVisitor()

    assert visitor.imports == []
    assert visitor.functions == []
    assert visitor.classes == []


def test_empty_module_produces_no_results() -> None:
    visitor = create_visitor("")

    assert visitor.imports == []
    assert visitor.functions == []
    assert visitor.classes == []


def test_module_with_only_expressions_produces_no_results() -> None:
    visitor = create_visitor(
        """
value = 10
message = "RepoArchitect"
result = value * 2
"""
    )

    assert visitor.imports == []
    assert visitor.functions == []
    assert visitor.classes == []

    