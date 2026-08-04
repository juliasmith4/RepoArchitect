from pathlib import Path

from .models import ParsedModule
from .visitor import PythonAstVisitor


class PythonParser:
    def parse(
        self,
        source: str,
        file_path: str,
    ) -> ParsedModule:
        tree = ast.parse(source)
        visitor = PythonAstVisitor()
        visitor.visit(tree)

        return ParsedModule(
            file_path=file_path,
            module_name=self._module_name_from_path(file_path),
            imports=visitor.imports,
            functions=visitor.functions,
            classes=visitor.classes,
            docstring=ast.get_docstring(tree),
        )

    @staticmethod
    def _module_name_from_path(file_path: str) -> str:
        path = Path(file_path).with_suffix("")
        parts = list(path.parts)

        if parts and parts[-1] == "__init__":
            parts.pop()

        return ".".join(parts)