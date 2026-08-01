"""Tests for the Python AST visitor."""

import ast

from app.analyzer.parsing.visitor import (
    PythonAstVisitor,
    expression_to_string,
    parse_parameters,
)


def create_visitor(source_code: str) -> PythonAstVisitor:
    """Parse source code and return a completed visitor."""

    syntax_tree = ast.parse(source_code)
    visitor = PythonAstVisitor()
    visitor.visit(syntax_tree)

    return visitor


# ---------------------------------------------------------------------------
# Expression conversion
# ---------------------------------------------------------------------------

def test_expression_to_string_returns_none_for_none() -> None:
    assert expression_to_string(None) is None



def test_expression_to_string_converts_name() -> None:
    expression = ast.parse("str", mode="eval").body

    assert expression_to_string(expression) == "str"



def test_expression_to_string_converts_complex_expression() -> None:
    expression = ast.parse(
        "dict[str, list[int]]",
        mode="eval",
    ).body

    assert expression_to_string(expression) == "dict[str, list[int]]"


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

    assert len(parameters) == 2
    assert parameters[0].name == "repository"
    assert parameters[1].name == "branch"


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
def analyze(repository: str, attempts: int = 3, enabled: bool = True):
    pass
"""
    )

    function = syntax_tree.body[0]
    assert isinstance(function, ast.FunctionDef)

    parameters = parse_parameters(function.args)

    assert parameters[0].default_value is None
    assert parameters[1].default_value == "3"
    assert parameters[2].default_value == "True"


def test_parse_parameters_aligns_defaults_with_final_parameters() -> None:
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
# Regular imports
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


def test_collects_multiple_regular_imports_from_one_statement() -> None:
    visitor = create_visitor(
        """
import os, sys, pathlib
"""
    )

    assert len(visitor.imports) == 3
    assert [item.module for item in visitor.imports] == [
        "os",
        "sys",
        "pathlib",
    ]


# ---------------------------------------------------------------------------
# From imports
# ---------------------------------------------------------------------------


def test_collects_from_import() -> None:
    visitor = create_visitor(
        """
from pathlib import Path
"""
    )

    assert len(visitor.imports) == 1

    imported_module = visitor.imports[0]

    assert imported_module.module == "pathlib"
    assert imported_module.names == ["Path"]
    assert imported_module.alias is None
    assert imported_module.line_number == 2
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


def test_collects_multiple_names_from_import() -> None:
    visitor = create_visitor(
        """
from typing import Any, Optional, Union
"""
    )

    assert len(visitor.imports) == 3
    assert [item.module for item in visitor.imports] == [
        "typing",
        "typing",
        "typing",
    ]
    assert [item.names for item in visitor.imports] == [
        ["Any"],
        ["Optional"],
        ["Union"],
    ]


def test_collects_relative_from_import() -> None:
    visitor = create_visitor(
        """
from .models import ParsedFunction
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == ".models"
    assert imported_module.names == ["ParsedFunction"]


def test_collects_relative_import_without_module_name() -> None:
    visitor = create_visitor(
        """
from . import models
"""
    )

    imported_module = visitor.imports[0]

    assert imported_module.module == "."
    assert imported_module.names == ["models"]


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
# Top-level functions
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


def test_collects_async_function() -> None:
    visitor = create_visitor(
        """
async def analyze_repository():
    pass
"""
    )

    assert len(visitor.functions) == 1

    function = visitor.functions[0]

    assert function.name == "analyze_repository"
    assert function.is_async is True
    assert function.is_method is False


def test_collects_multiple_top_level_functions() -> None:
    visitor = create_visitor(
        """
def first():
    pass


def second():
    pass


async def third():
    pass
"""
    )

    assert [function.name for function in visitor.functions] == [
        "first",
        "second",
        "third",
    ]


def test_collects_function_parameters() -> None:
    visitor = create_visitor(
        """
def analyze(path: str, depth: int = 3):
    pass
"""
    )

    function = visitor.functions[0]

    assert len(function.parameters) == 2

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

    function = visitor.functions[0]

    assert function.return_annotation == "list[str]"


def test_function_without_return_annotation_uses_none() -> None:
    visitor = create_visitor(
        """
def get_dependencies():
    return []
"""
    )

    assert visitor.functions[0].return_annotation is None


def test_collects_function_decorators() -> None:
    visitor = create_visitor(
        """
@cache
@validate(enabled=True)
def analyze_repository():
    pass
"""
    )

    function = visitor.functions[0]

    assert function.decorators == [
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

    function = visitor.functions[0]

    assert function.docstring == "Analyze the supplied repository."


def test_function_without_docstring_uses_none() -> None:
    visitor = create_visitor(
        """
def analyze_repository():
    pass
"""
    )

    assert visitor.functions[0].docstring is None


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


def test_function_after_nested_function_is_still_collected() -> None:
    visitor = create_visitor(
        """
def outer():
    def inner():
        pass


def another_function():
    pass
"""
    )

    assert [function.name for function in visitor.functions] == [
        "outer",
        "another_function",
    ]


# ---------------------------------------------------------------------------
# Classes
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

    parsed_class = visitor.classes[0]

    assert parsed_class.base_classes == [
        "BaseAnalyzer",
        "Serializable",
    ]


def test_collects_complex_class_base_class() -> None:
    visitor = create_visitor(
        """
class RepositoryCollection(list[Repository]):
    pass
"""
    )

    assert visitor.classes[0].base_classes == [
        "list[Repository]",
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

    parsed_class = visitor.classes[0]

    assert parsed_class.decorators == [
        "dataclass",
        "register('repository')",
    ]


def test_collects_class_docstring() -> None:
    visitor = create_visitor(
        '''
class RepositoryAnalyzer:
    """Analyze the architecture of a repository."""
'''
    )

    parsed_class = visitor.classes[0]

    assert (
        parsed_class.docstring
        == "Analyze the architecture of a repository."
    )


def test_collects_class_line_numbers() -> None:
    visitor = create_visitor(
        """class RepositoryAnalyzer:
    def analyze(self):
        return True
"""
    )

    parsed_class = visitor.classes[0]

    assert parsed_class.start_line == 1
    assert parsed_class.end_line == 3


# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------


def test_collects_method_inside_class() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def analyze(self):
        pass
"""
    )

    parsed_class = visitor.classes[0]

    assert len(parsed_class.methods) == 1

    method = parsed_class.methods[0]

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


def test_collects_method_parameters() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def analyze(
        self,
        path: str,
        include_tests: bool = False,
    ) -> dict[str, object]:
        pass
"""
    )

    method = visitor.classes[0].methods[0]

    assert [parameter.name for parameter in method.parameters] == [
        "self",
        "path",
        "include_tests",
    ]
    assert method.parameters[1].annotation == "str"
    assert method.parameters[2].annotation == "bool"
    assert method.parameters[2].default_value == "False"
    assert method.return_annotation == "dict[str, object]"


def test_collects_method_decorators() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    @classmethod
    @cache
    def create(cls):
        pass
"""
    )

    method = visitor.classes[0].methods[0]

    assert method.decorators == [
        "classmethod",
        "cache",
    ]


def test_nested_function_inside_method_is_ignored() -> None:
    visitor = create_visitor(
        """
class RepositoryAnalyzer:
    def analyze(self):
        def normalize_path(path):
            return path

        return normalize_path("repository")
"""
    )

    parsed_class = visitor.classes[0]

    assert len(parsed_class.methods) == 1
    assert parsed_class.methods[0].name == "analyze"


# ---------------------------------------------------------------------------
# Nested classes
# ---------------------------------------------------------------------------


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

    assert outer_class.name == "Outer"
    assert outer_class.parent_class is None

    assert inner_class.name == "Inner"
    assert inner_class.parent_class == "Outer"


def test_collects_method_inside_nested_class() -> None:
    visitor = create_visitor(
        """
class Outer:
    class Inner:
        def analyze(self):
            pass
"""
    )

    inner_class = visitor.classes[1]

    assert len(inner_class.methods) == 1
    assert inner_class.methods[0].name == "analyze"
    assert inner_class.methods[0].parent_class == "Inner"


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
    assert visitor.functions[0].name == "build_analyzer"
    assert visitor.classes == []


# ---------------------------------------------------------------------------
# Complete module
# ---------------------------------------------------------------------------


def test_collects_complete_module_structure() -> None:
    visitor = create_visitor(
        '''
import os
from pathlib import Path

DEFAULT_DEPTH = 3


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
        return {}
'''
    )

    assert len(visitor.imports) == 2
    assert len(visitor.functions) == 1
    assert len(visitor.classes) == 1

    assert visitor.imports[0].module == "os"
    assert visitor.imports[1].module == "pathlib"
    assert visitor.imports[1].names == ["Path"]

    top_level_function = visitor.functions[0]

    assert top_level_function.name == "normalize_path"
    assert top_level_function.return_annotation == "Path"
    assert (
        top_level_function.docstring
        == "Normalize a repository path."
    )

    parsed_class = visitor.classes[0]

    assert parsed_class.name == "RepositoryAnalyzer"
    assert parsed_class.docstring == "Analyze Python repositories."
    assert len(parsed_class.methods) == 2

    constructor = parsed_class.methods[0]
    analyze_method = parsed_class.methods[1]

    assert constructor.name == "__init__"
    assert constructor.is_async is False
    assert constructor.parent_class == "RepositoryAnalyzer"

    assert analyze_method.name == "analyze"
    assert analyze_method.is_async is True
    assert analyze_method.return_annotation == "dict[str, object]"
    assert analyze_method.parameters[1].name == "include_tests"
    assert analyze_method.parameters[1].default_value == "False"






    