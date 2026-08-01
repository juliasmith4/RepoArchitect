"""AST visitor for extracting structured data from Python source code."""

import ast

from .models import (
    ImportInfo,
    ParsedClass,
    ParsedFunction,
    ParsedParameter,
)


def expression_to_string(node: ast.AST | None) -> str | None:
    """Convert an AST expression into readable Python source code."""

    if node is None:
        return None

    try:
        return ast.unparse(node)
    except (TypeError, ValueError):
        return None


def parse_parameters(arguments: ast.arguments) -> list[ParsedParameter]:
    """Convert function arguments into ParsedParameter objects."""

    parameters: list[ParsedParameter] = []

    # Positional-only and regular positional parameters are handled together.
    positional_arguments = [
        *arguments.posonlyargs,
        *arguments.args,
    ]

    # Python stores defaults only for the final positional parameters.
    default_offset = len(positional_arguments) - len(arguments.defaults)

    for index, argument in enumerate(positional_arguments):
        default_node: ast.expr | None = None

        if index >= default_offset:
            default_index = index - default_offset
            default_node = arguments.defaults[default_index]

        parameters.append(
            ParsedParameter(
                name=argument.arg,
                annotation=expression_to_string(argument.annotation),
                default_value=expression_to_string(default_node),
            )
        )

    # Collect *args.
    if arguments.vararg is not None:
        parameters.append(
            ParsedParameter(
                name=f"*{arguments.vararg.arg}",
                annotation=expression_to_string(
                    arguments.vararg.annotation
                ),
                default_value=None,
            )
        )

    # Collect keyword-only parameters.
    for argument, default_node in zip(
        arguments.kwonlyargs,
        arguments.kw_defaults,
        strict=True,
    ):
        parameters.append(
            ParsedParameter(
                name=argument.arg,
                annotation=expression_to_string(argument.annotation),
                default_value=expression_to_string(default_node),
            )
        )

    # Collect **kwargs.
    if arguments.kwarg is not None:
        parameters.append(
            ParsedParameter(
                name=f"**{arguments.kwarg.arg}",
                annotation=expression_to_string(
                    arguments.kwarg.annotation
                ),
                default_value=None,
            )
        )

    return parameters


class PythonAstVisitor(ast.NodeVisitor):
    """Collect structured information from a Python AST."""

    def __init__(self) -> None:
        self.imports: list[ImportInfo] = []
        self.functions: list[ParsedFunction] = []
        self.classes: list[ParsedClass] = []

        # Holds the classes that the visitor is currently inside.
        self._class_stack: list[ParsedClass] = []

        # Prevents nested functions from being treated as top-level functions.
        self._function_depth = 0

    def visit_Import(self, node: ast.Import) -> None:
        """Collect regular import statements."""

        for imported_name in node.names:
            self.imports.append(
                ImportInfo(
                    module=imported_name.name,
                    names=[],
                    alias=imported_name.asname,
                    line_number=node.lineno,
                    is_from_import=False,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Collect from-import statements."""

        # node.module can be None for relative imports such as:
        # from . import models
        module = node.module or ""

        # Preserve the leading dots for relative imports.
        if node.level > 0:
            module = f"{'.' * node.level}{module}"

        for imported_name in node.names:
            self.imports.append(
                ImportInfo(
                    module=module,
                    names=[imported_name.name],
                    alias=imported_name.asname,
                    line_number=node.lineno,
                    is_from_import=True,
                )
            )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Collect a synchronous function definition."""

        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        """Collect an asynchronous function definition."""

        self._visit_function(node, is_async=True)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect a class and its directly defined methods."""

        # Ignore classes declared inside functions for the first version.
        if self._function_depth > 0:
            return

        parent_class = (
            self._class_stack[-1].name
            if self._class_stack
            else None
        )

        parsed_class = ParsedClass(
            name=node.name,
            base_classes=[
                expression
                for base in node.bases
                if (expression := expression_to_string(base)) is not None
            ],
            methods=[],
            decorators=[
                expression
                for decorator in node.decorator_list
                if (
                    expression := expression_to_string(decorator)
                ) is not None
            ],
            docstring=ast.get_docstring(node),
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", None),
            parent_class=parent_class,
        )

        self.classes.append(parsed_class)
        self._class_stack.append(parsed_class)

        try:
            self.generic_visit(node)
        finally:
            self._class_stack.pop()

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        is_async: bool,
    ) -> None:
        """Create and store a ParsedFunction from a function AST node."""

        # A function found while already inside another function is nested.
        # RepoArchitect can support nested functions later.
        is_nested_function = self._function_depth > 0

        if not is_nested_function:
            parent_class = (
                self._class_stack[-1].name
                if self._class_stack
                else None
            )

            parsed_function = ParsedFunction(
                name=node.name,
                parameters=parse_parameters(node.args),
                decorators=[
                    expression
                    for decorator in node.decorator_list
                    if (
                        expression := expression_to_string(decorator)
                    ) is not None
                ],
                return_annotation=expression_to_string(node.returns),
                docstring=ast.get_docstring(node),
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", None),
                is_async=is_async,
                is_method=bool(self._class_stack),
                parent_class=parent_class,
            )

            if self._class_stack:
                self._class_stack[-1].methods.append(parsed_function)
            else:
                self.functions.append(parsed_function)

        self._function_depth += 1

        try:
            self.generic_visit(node)
        finally:
            self._function_depth -= 1