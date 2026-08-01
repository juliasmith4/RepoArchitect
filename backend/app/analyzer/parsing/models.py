"""Data models produced by the Python AST parser."""

from dataclasses import dataclass, field


@dataclass
class ImportInfo:
    """Information about an imported module or object."""

    module: str
    names: list[str]
    alias: str | None
    line_number: int
    is_from_import: bool


@dataclass
class ParsedParameter:
    """A parameter declared by a function or method."""

    name: str
    annotation: str | None
    default_value: str | None


@dataclass
class ParsedCall:
    """A function or method call found in source code."""

    name: str
    line_number: int

@dataclass
class ParsedAssignment:
    """An assignment found inside a function or method."""

    target: str
    value: str | None
    line_number: int
    is_instance_attribute: bool


@dataclass
class ParsedFunction:
    """A parsed function or class method."""

    name: str
    parameters: list[ParsedParameter]
    decorators: list[str]
    return_annotation: str | None
    docstring: str | None
    start_line: int
    end_line: int | None
    is_async: bool
    is_method: bool
    parent_class: str | None
    calls: list[ParsedCall] = field(default_factory=list)
    assignments: list[ParsedAssignment] = field(default_factory=list)

@dataclass
class ParsedClass:
    """A parsed Python class."""

    name: str
    base_classes: list[str]
    methods: list[ParsedFunction]
    decorators: list[str]
    docstring: str | None
    start_line: int
    end_line: int | None
    parent_class: str | None

