"""Parse Python source files into structured models."""

import ast
from pathlib import Path

from .models import ParsedModule
from .visitor import PythonAstVisitor


class PythonParser:
    """Parse Python source code into ParsedModule objects."""

    def parse(
        self,
        source: str,
        path: Path,
        repository_root: Path,
    ) -> ParsedModule:
        module_name = self._module_name_from_path(
            path=path,
            repository_root=repository_root,
        )

        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            return ParsedModule(
                path=path,
                module_name=module_name,
                parse_error=str(error),
            )

        visitor = PythonAstVisitor()
        visitor.visit(tree)

        return ParsedModule(
            path=path,
            module_name=module_name,
            imports=visitor.imports,
            functions=visitor.functions,
            classes=visitor.classes,
            docstring=ast.get_docstring(tree),
        )

    @staticmethod
    def _module_name_from_path(
        path: Path,
        repository_root: Path,
    ) -> str:
        relative_path = path.relative_to(repository_root)

        if relative_path.suffix == ".py":
            relative_path = relative_path.with_suffix("")

        parts = list(relative_path.parts)

        if parts and parts[-1] == "__init__":
            parts.pop()

        return ".".join(parts)