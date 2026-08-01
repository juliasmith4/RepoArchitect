"""Tests for the Python AST visitor."""

import ast

from app.analyzer.parsing.visitor import (
    PythonAstVisitor,
    expression_to_string,
    get_call_name,
    parse_parameters,
)


def create_visitor(source_code: str) -> PythonAstVisitor:
    """Parse source code and return a completed visitor."""

    syntax_tree = ast.parse(source_code)

    visitor = PythonAstVisitor()
    visitor.visit(syntax_tree)

    return visitor


# ---------------------------------------------------------------------------
# Expression helpers
# ---------------------------------------------------------------------------


def test_expression_to_string_returns_none_for_none() -> None:
    assert expression_to_string(None) is None


def test_expression_to_string_converts_simple_expression() -> None:
    expression = ast.parse("list[str]", mode="eval").body

    assert expression_to_string(expression) == "list[str]"


def test_get_call_name_collects_direct_function_name() -> None:
    call = ast.parse("parse_repository()", mode="eval").body

    assert isinstance(call, ast.Call)
    assert get_call_name(call.func) == "parse_repository"


def test_get_call_name_collects_method_name() -> None:
    call = ast.parse("repository.save()", mode="eval").body

    assert isinstance(call, ast.Call)
    assert get_call_name(call.func) == "repository.save"


def test_get_call_name_collects_chained_method_name() -> None:
    call = ast.parse(
        "self.database.session.commit()",
        mode="eval",
    ).body

    assert isinstance(call, ast.Call)
    assert (
        get_call_name(call.func)
        == "self.database.session.commit"
    )


def test_get_call_name_returns_none_for_unsupported_expression() -> None:
    call = ast.parse("(get_handler())()", mode="eval").body

    assert isinstance(call, ast.Call)
    assert get_call_name(call.func) is None


# ---------------------------------------------------------------------------
# Parameter parsing
# ---------------------------------------------------------------------------


def test_parse_parameters_collects_regular_parameters() -> None:
    syntax_tree = ast.parse(
        """
def analyze(repository, branch):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert [parameter.name for parameter in parameters] == [
        "repository",
        "branch",
    ]


def test_parse_parameters_collects_annotations() -> None:
    syntax_tree = ast.parse(
        """
def analyze(repository: str, attempts: int):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert parameters[0].annotation == "str"
    assert parameters[1].annotation == "int"


def test_parse_parameters_collects_defaults() -> None:
    syntax_tree = ast.parse(
        """
def analyze(
    repository: str,
    attempts: int = 3,
    enabled: bool = True,
):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert parameters[0].default_value is None
    assert parameters[1].default_value == "3"
    assert parameters[2].default_value == "True"


def test_parse_parameters_aligns_defaults_to_final_parameters() -> None:
    syntax_tree = ast.parse(
        """
def analyze(first, second, third="default"):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert parameters[0].default_value is None
    assert parameters[1].default_value is None
    assert parameters[2].default_value == "'default'"


def test_parse_parameters_collects_positional_only_parameters() -> None:
    syntax_tree = ast.parse(
        """
def analyze(repository, /, branch):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert [parameter.name for parameter in parameters] == [
        "repository",
        "branch",
    ]


def test_parse_parameters_collects_varargs() -> None:
    syntax_tree = ast.parse(
        """
def analyze(*files: str):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert len(parameters) == 1
    assert parameters[0].name == "*files"
    assert parameters[0].annotation == "str"
    assert parameters[0].default_value is None


def test_parse_parameters_collects_keyword_only_parameters() -> None:
    syntax_tree = ast.parse(
        """
def analyze(*, include_tests: bool = False):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert len(parameters) == 1
    assert parameters[0].name == "include_tests"
    assert parameters[0].annotation == "bool"
    assert parameters[0].default_value == "False"


def test_parse_parameters_collects_required_keyword_only_parameter() -> None:
    syntax_tree = ast.parse(
        """
def analyze(*, repository: str):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert parameters[0].name == "repository"
    assert parameters[0].annotation == "str"
    assert parameters[0].default_value is None


def test_parse_parameters_collects_kwargs() -> None:
    syntax_tree = ast.parse(
        """
def analyze(**options: object):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert len(parameters) == 1
    assert parameters[0].name == "**options"
    assert parameters[0].annotation == "object"
    assert parameters[0].default_value is None


def test_parse_parameters_collects_complete_signature() -> None:
    syntax_tree = ast.parse(
        """
def analyze(
    repository: str,
    attempts: int = 3,
    *files: str,
    include_tests: bool = False,
    **options: object,
):
    pass
"""
    )

    function = syntax_tree.body[0]

    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert [parameter.name for parameter in parameters] == [
        "repository",
        "attempts",
        "*files",
        "include_tests",
        "**options",
    ]

    assert [parameter.annotation for parameter in parameters] == [
        "str",
        "int",
        "str",
        "bool",
        "object",
    ]

    assert [parameter.default_value for parameter in parameters] == [
        None,
        "3",
        None,
        "False",
        None,
    ]


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


def test_collects_regular_import() -> None:
    visitor = create_visitor(
        """
import os
"""
    )

    assert len(visitor.imports) == 1

    imported_module = visitor.imports[0]

    assert imported_module.module == "os"
    assert imported_module.names == []
    assert imported_module.alias is None
    assert imported_module.line_number == 2
    assert imported_module.is_from_import is False


def test_collects_aliased_import() -> None:
    visitor = create_visitor(
        """
import numpy as np
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == "numpy"
    assert imported_module.alias == "np"


def test_collects_multiple_regular_imports() -> None:
    visitor = create_visitor(
        """
import os, sys, pathlib
"""
    )

    assert [item.module for item in visitor.imports] == [
        "os",
        "sys",
        "pathlib",
    ]


def test_collects_from_import() -> None:
    visitor = create_visitor(
        """
from pathlib import Path
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == "pathlib"
    assert imported_module.names == ["Path"]
    assert imported_module.alias is None
    assert imported_module.is_from_import is True


def test_collects_aliased_from_import() -> None:
    visitor = create_visitor(
        """
from pandas import DataFrame as Frame
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == "pandas"
    assert imported_module.names == ["DataFrame"]
    assert imported_module.alias == "Frame"


def test_collects_multiple_from_import_names() -> None:
    visitor = create_visitor(
        """
from typing import Any, Optional, Union
"""
    )

    assert [item.names for item in visitor.imports] == [
        ["Any"],
        ["Optional"],
        ["Union"],
    ]


def test_collects_relative_import() -> None:
    visitor = create_visitor(
        """
from .models import ParsedFunction
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == ".models"
    assert imported_module.names == ["ParsedFunction"]


def test_collects_parent_relative_import() -> None:
    visitor = create_visitor(
        """
from ..services.parser import ParserService
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == "..services.parser"
    assert imported_module.names == ["ParserService"]


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def test_collects_regular_function() -> None:
    visitor = create_visitor(
        """
def analyze_repository():
    pass
"""
    )

    assert len(visitor.functions) == 1

    function = visitor.functions[0]

    assert function.name == "analyze_repository"
    assert function.is_async is False
    assert function.is_method is False
    assert function.parent_class is None
    assert function.calls == []


def test_collects_async_function() -> None:
    visitor = create_visitor(
        """
async def analyze_repository():
    pass
"""
    )

    function = visitor.functions[0]

    assert function.name == "analyze_repository"
    assert function.is_async is True


def test_collects_function_parameters() -> None:
    visitor = create_visitor(
        """
def analyze(path: str, depth: int = 3):
    pass
"""
    )

    function = visitor.functions[0]

    assert function.parameters[0].name == "path"
    assert function.parameters[0].annotation == "str"
    assert function.parameters[0].default_value is None

    assert function.parameters[1].name == "depth"
    assert function.parameters[1].annotation == "int"
    assert function.parameters[1].default_value == "3"


def test_collects_function_return_annotation() -> None:
    visitor = create_visitor(
        """
def get_dependencies() -> list[str]:
    return []
"""
    )

    assert visitor.functions[0].return_annotation == "list[str]"


def test_collects_function_decorators() -> None:
    visitor = create_visitor(
        """
@cache
@validate(enabled=True)
def analyze_repository():
    pass
"""
    )

    assert visitor.functions[0].decorators == [
        "cache",
        "validate(enabled=True)",
    ]


def test_collects_function_docstring() -> None:
    visitor = create_visitor(
        '''
def analyze_repository():
    """Analyze the supplied repository."""

    pass
'''
    )

    assert (
        visitor.functions[0].docstring
        == "Analyze the supplied repository."
    )


def test_collects_function_line_numbers() -> None:
    visitor = create_visitor(
        """def analyze_repository():
    value = 1
    return value
"""
    )

    function = visitor.functions[0]

    assert function.start_line == 1
    assert function.end_line == 3


def test_nested_function_is_not_added_as_top_level_function() -> None:
    visitor = create_visitor(
        """
def outer():
    def inner():
        pass

    inner()
"""
    )

    assert len(visitor.functions) == 1
    assert visitor.functions[0].name == "outer"


# ---------------------------------------------------------------------------
# Function calls
# ---------------------------------------------------------------------------


def test_collects_direct_function_call() -> None:
    visitor = create_visitor(
        """
def analyze():
    parse_repository()
"""
    )

    function = visitor.functions[0]

    assert len(function.calls) == 1
    assert function.calls[0].name == "parse_repository"
    assert function.calls[0].line_number == 3


def test_collects_method_call() -> None:
    visitor = create_visitor(
        """
def analyze(repository):
    repository.save()
"""
    )

    function = visitor.functions[0]

    assert len(function.calls) == 1
    assert function.calls[0].name == "repository.save"
    assert function.calls[0].line_number == 3


def test_collects_chained_method_call() -> None:
    visitor = create_visitor(
        """
def analyze(client):
    client.repositories.create()
"""
    )

    assert (
        visitor.functions[0].calls[0].name
        == "client.repositories.create"
    )


def test_collects_multiple_calls_in_function() -> None:
    visitor = create_visitor(
        """
def analyze(path):
    repository = parse_repository(path)
    validate_repository(repository)
    repository.save()
"""
    )

    function = visitor.functions[0]

    assert [call.name for call in function.calls] == [
        "parse_repository",
        "validate_repository",
        "repository.save",
    ]


def test_collects_nested_calls() -> None:
    visitor = create_visitor(
        """
def analyze(path):
    save_repository(parse_repository(path))
"""
    )

    function = visitor.functions[0]

    assert [call.name for call in function.calls] == [
        "save_repository",
        "parse_repository",
    ]


def test_collects_calls_inside_control_flow() -> None:
    visitor = create_visitor(
        """
def analyze(repository):
    if repository.is_valid():
        repository.save()
"""
    )

    function = visitor.functions[0]

    assert [call.name for call in function.calls] == [
        "repository.is_valid",
        "repository.save",
    ]


def test_calls_do_not_leak_between_functions() -> None:
    visitor = create_visitor(
        """
def first():
    load_repository()


def second():
    save_repository()
"""
    )

    first_function = visitor.functions[0]
    second_function = visitor.functions[1]

    assert [call.name for call in first_function.calls] == [
        "load_repository",
    ]

    assert [call.name for call in second_function.calls] == [
        "save_repository",
    ]


def test_call_inside_nested_function_is_attached_to_outer_function() -> None:
    visitor = create_visitor(
        """
def outer():
    def inner():
        save_repository()

    inner()
"""
    )

    function = visitor.functions[0]

    assert [call.name for call in function.calls] == [
        "save_repository",
        "inner",
    ]

# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


def test_collects_local_variable_assignment() -> None:
    visitor = create_visitor(
        """
def analyze(path):
    result = parse_repository(path)
"""
    )

    function = visitor.functions[0]

    assert len(function.assignments) == 1

    assignment = function.assignments[0]

    assert assignment.target == "result"
    assert assignment.value == "parse_repository(path)"
    assert assignment.line_number == 3
    assert assignment.is_instance_attribute is False


def test_collects_instance_attribute_assignment() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def __init__(self, parser):
        self.parser = parser
"""
    )

    constructor = visitor.classes[0].methods[0]

    assert len(constructor.assignments) == 1

    assignment = constructor.assignments[0]

    assert assignment.target == "self.parser"
    assert assignment.value == "parser"
    assert assignment.line_number == 4
    assert assignment.is_instance_attribute is True


def test_collects_constructor_call_assignment() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def __init__(self):
        self.parser = PythonParser()
"""
    )

    constructor = visitor.classes[0].methods[0]

    assert len(constructor.assignments) == 1

    assignment = constructor.assignments[0]

    assert assignment.target == "self.parser"
    assert assignment.value == "PythonParser()"
    assert assignment.is_instance_attribute is True

    assert [call.name for call in constructor.calls] == [
        "PythonParser",
    ]


def test_collects_multiple_assignment_targets() -> None:
    visitor = create_visitor(
        """
def create_values():
    first = second = build_value()
"""
    )

    function = visitor.functions[0]

    assert [assignment.target for assignment in function.assignments] == [
        "first",
        "second",
    ]

    assert [assignment.value for assignment in function.assignments] == [
        "build_value()",
        "build_value()",
    ]


def test_collects_annotated_assignment() -> None:
    visitor = create_visitor(
        """
def analyze():
    result: AnalysisResult = create_result()
"""
    )

    function = visitor.functions[0]

    assert len(function.assignments) == 1

    assignment = function.assignments[0]

    assert assignment.target == "result"
    assert assignment.value == "create_result()"
    assert assignment.line_number == 3
    assert assignment.is_instance_attribute is False


def test_collects_annotated_instance_attribute_assignment() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def __init__(self, parser):
        self.parser: PythonParser = parser
"""
    )

    constructor = visitor.classes[0].methods[0]
    assignment = constructor.assignments[0]

    assert assignment.target == "self.parser"
    assert assignment.value == "parser"
    assert assignment.is_instance_attribute is True


def test_collects_assignment_without_value() -> None:
    visitor = create_visitor(
        """
def analyze():
    result: AnalysisResult
"""
    )

    assignment = visitor.functions[0].assignments[0]

    assert assignment.target == "result"
    assert assignment.value is None
    assert assignment.is_instance_attribute is False


def test_assignments_do_not_leak_between_functions() -> None:
    visitor = create_visitor(
        """
def first():
    result = load_repository()


def second():
    result = save_repository()
"""
    )

    first_function = visitor.functions[0]
    second_function = visitor.functions[1]

    assert [assignment.value for assignment in first_function.assignments] == [
        "load_repository()",
    ]

    assert [assignment.value for assignment in second_function.assignments] == [
        "save_repository()",
    ]


def test_assignments_do_not_leak_between_methods() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def load(self):
        self.result = load_repository()

    def save(self):
        self.result = save_repository()
"""
    )

    parsed_class = visitor.classes[0]

    load_method = parsed_class.methods[0]
    save_method = parsed_class.methods[1]

    assert [assignment.value for assignment in load_method.assignments] == [
        "load_repository()",
    ]

    assert [assignment.value for assignment in save_method.assignments] == [
        "save_repository()",
    ]


def test_collects_assignment_inside_control_flow() -> None:
    visitor = create_visitor(
        """
def analyze(repository):
    if repository.is_valid():
        result = repository.parse()
"""
    )

    assignment = visitor.functions[0].assignments[0]

    assert assignment.target == "result"
    assert assignment.value == "repository.parse()"


def test_ignores_unsupported_subscript_assignment_target() -> None:
    visitor = create_visitor(
        """
def configure(config):
    config["timeout"] = 30
"""
    )

    function = visitor.functions[0]

    assert function.assignments == []

    
# ---------------------------------------------------------------------------
# Classes and methods
# ---------------------------------------------------------------------------


def test_collects_class() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    pass
"""
    )

    assert len(visitor.classes) == 1

    parsed_class = visitor.classes[0]

    assert parsed_class.name == "RepositoryAnalyzer"
    assert parsed_class.base_classes == []
    assert parsed_class.methods == []
    assert parsed_class.decorators == []
    assert parsed_class.parent_class is None


def test_collects_class_base_classes() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer(BaseAnalyzer, Serializable):
    pass
"""
    )

    assert visitor.classes[0].base_classes == [
        "BaseAnalyzer",
        "Serializable",
    ]


def test_collects_class_decorators() -> None:
    visitor = create_visitor(
        """
@dataclass
@register("repository")
class RepositoryAnalyzer:
    pass
"""
    )

    assert visitor.classes[0].decorators == [
        "dataclass",
        "register('repository')",
    ]


def test_collects_class_docstring() -> None:
    visitor = create_visitor(
        '''
class RepositoryAnalyzer:
    """Analyze repository architecture."""
'''
    )

    assert (
        visitor.classes[0].docstring
        == "Analyze repository architecture."
    )


def test_collects_method_inside_class() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def analyze(self):
        pass
"""
    )

    parsed_class = visitor.classes[0]
    method = parsed_class.methods[0]

    assert len(parsed_class.methods) == 1
    assert method.name == "analyze"
    assert method.is_method is True
    assert method.is_async is False
    assert method.parent_class == "RepositoryAnalyzer"


def test_method_is_not_added_to_top_level_functions() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def analyze(self):
        pass
"""
    )

    assert visitor.functions == []
    assert len(visitor.classes[0].methods) == 1


def test_collects_async_method() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    async def analyze(self):
        pass
"""
    )

    method = visitor.classes[0].methods[0]

    assert method.name == "analyze"
    assert method.is_async is True
    assert method.is_method is True


def test_collects_calls_inside_method() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def analyze(self):
        self.load_repository()
        self.database.commit()
"""
    )

    method = visitor.classes[0].methods[0]

    assert [call.name for call in method.calls] == [
        "self.load_repository",
        "self.database.commit",
    ]


def test_method_calls_do_not_leak_between_methods() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def load(self):
        self.repository.load()

    def save(self):
        self.repository.save()
"""
    )

    parsed_class = visitor.classes[0]

    load_method = parsed_class.methods[0]
    save_method = parsed_class.methods[1]

    assert [call.name for call in load_method.calls] == [
        "self.repository.load",
    ]

    assert [call.name for call in save_method.calls] == [
        "self.repository.save",
    ]


def test_collects_nested_class_with_parent_class() -> None:
    visitor = create_visitor(
        """
class Outer:
    class Inner:
        pass
"""
    )

    assert len(visitor.classes) == 2

    outer_class = visitor.classes[0]
    inner_class = visitor.classes[1]

    assert outer_class.parent_class is None
    assert inner_class.parent_class == "Outer"


def test_ignores_class_declared_inside_function() -> None:
    visitor = create_visitor(
        """
def build_analyzer():
    class LocalAnalyzer:
        pass

    return LocalAnalyzer
"""
    )

    assert len(visitor.functions) == 1
    assert visitor.classes == []


# ---------------------------------------------------------------------------
# Complete module
# ---------------------------------------------------------------------------


def test_collects_complete_module_structure() -> None:
    visitor = create_visitor(
        '''
import os
from pathlib import Path


def normalize_path(path: str) -> Path:
    """Normalize a repository path."""

    return Path(path)


class RepositoryAnalyzer:
    """Analyze Python repositories."""

    def __init__(self, repository_path: Path):
        self.repository_path = repository_path

    async def analyze(
        self,
        include_tests: bool = False,
    ) -> dict[str, object]:
        normalized_path = normalize_path(
            str(self.repository_path)
        )
        return self.parser.parse(normalized_path)
'''
    )

    assert len(visitor.imports) == 2
    assert len(visitor.functions) == 1
    assert len(visitor.classes) == 1

    normalize_function = visitor.functions[0]

    assert normalize_function.name == "normalize_path"
    assert normalize_function.return_annotation == "Path"
    assert [call.name for call in normalize_function.calls] == [
        "Path",
    ]

    parsed_class = visitor.classes[0]

    assert parsed_class.name == "RepositoryAnalyzer"
    assert len(parsed_class.methods) == 2

    constructor = parsed_class.methods[0]
    analyze_method = parsed_class.methods[1]

    assert constructor.name == "__init__"
    assert constructor.calls == []

    assert analyze_method.name == "analyze"
    assert analyze_method.is_async is True
    assert analyze_method.return_annotation == "dict[str, object]"

    assert [call.name for call in analyze_method.calls] == [
        "normalize_path",
        "str",
        "self.parser.parse",
    ]