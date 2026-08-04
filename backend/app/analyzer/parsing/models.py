"""Data models produced by the Python AST parser."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ImportInfo:
    """Information about an imported module or object."""

    module: str
    names: list[str] = field(default_factory=list)
    alias: str | None = None
    line_number: int = 0
    is_from_import: bool = False


@dataclass(slots=True)
class ParsedParameter:
    """A parameter declared by a function or method."""

    name: str
    annotation: str | None = None
    default_value: str | None = None


@dataclass(slots=True)
class ParsedCall:
    """A function or method call found in source code."""

    name: str
    line_number: int = 0


@dataclass(slots=True)
class ParsedAssignment:
    """An assignment found inside a function or method."""

    target: str
    value: str | None = None
    line_number: int = 0
    is_instance_attribute: bool = False


@dataclass(slots=True)
class ParsedReturn:
    """A return statement found inside a function or method."""

    value: str | None = None
    line_number: int = 0


@dataclass(slots=True)
class ParsedFunction:
    """A parsed function or class method."""

    name: str
    parameters: list[ParsedParameter] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    return_annotation: str | None = None
    docstring: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    is_async: bool = False
    is_method: bool = False
    parent_class: str | None = None
    calls: list[ParsedCall] = field(default_factory=list)
    assignments: list[ParsedAssignment] = field(default_factory=list)
    returns: list[ParsedReturn] = field(default_factory=list)

    @property
    def line_count(self) -> int | None:
        """Return the inclusive number of lines occupied by the function."""

        if self.start_line is None or self.end_line is None:
            return None

        return self.end_line - self.start_line + 1


@dataclass(slots=True)
class ParsedClass:
    """A parsed Python class."""

    name: str
    base_classes: list[str] = field(default_factory=list)
    methods: list[ParsedFunction] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    parent_class: str | None = None

    @property
    def line_count(self) -> int | None:
        """Return the inclusive number of lines occupied by the class."""

        if self.start_line is None or self.end_line is None:
            return None

        return self.end_line - self.start_line + 1

    @property
    def method_count(self) -> int:
        """Return the number of methods directly stored on the class."""

        return len(self.methods)


@dataclass(slots=True)
class ParsedModule:
    """The complete parsed representation of one Python source file."""

    path: Path
    module_name: str
    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[ParsedFunction] = field(default_factory=list)
    classes: list[ParsedClass] = field(default_factory=list)
    docstring: str | None = None
    parse_error: str | None = None
    @property
    def file_path(self) -> str:
        """Return the path as a string for graph and API output."""

        return str(self.path)

    @property
    def import_count(self) -> int:
        """Return the number of parsed import entries."""

        return len(self.imports)

    @property
    def function_count(self) -> int:
        """Return the number of top-level functions."""

        return len(self.functions)

    @property
    def class_count(self) -> int:
        """Return the number of parsed classes."""

        return len(self.classes)

    @property
    def method_count(self) -> int:
        """Return the total number of methods across all classes."""

        return sum(
            parsed_class.method_count
            for parsed_class in self.classes
        )

    @property
    def was_parsed_successfully(self) -> bool:
        """Return whether parsing completed without a syntax error."""

        return self.parse_error is None


# Backward-compatible name used by existing tests and older code.
ParsedFile = ParsedModule