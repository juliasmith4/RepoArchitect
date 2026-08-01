"""High-level interface for parsing Python source files."""

import ast
from pathlib import Path

from .models import ParsedModule
from .visitor import PythonAstVisitor


class RepoArchitect:
    """Parse Python source code into structured architecture data."""

    def parse_source(
        self,
        source_code: str,
        *,
        file_path: str | None = None,
    ) -> ParsedModule:
        tree = ast.parse(source_code)

        visitor = PythonAstVisitor()
        visitor.visit(tree)

        return ParsedModule(
            file_path=file_path,
            imports=visitor.imports,
            functions=visitor.functions,
            classes=visitor.classes,
        )

    def parse_file(self, file_path: str | Path) -> ParsedModule:
        path = Path(file_path)

        source_code = path.read_text(encoding="utf-8")

        return self.parse_source(
            source_code,
            file_path=str(path),
        )