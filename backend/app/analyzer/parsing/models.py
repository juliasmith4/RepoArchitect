from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ImportInfo:
    """Represents a Python import statement."""
    module: str
    names: list[str] = field(default_factory=list)
    alias: str | None = None
    line_number: int | None = None
    is_from_import: bool = False



@dataclass(slots=True)
class ParsedParameter:
    """Represents a function or method parameter."""

    name: str
    annotation: str | None = None
    default_value: str | None = None



@dataclass(slots=True)
class ParsedFunction:
    """Represents a function or method found in a Python file."""

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
    parent_function: str | None = None


    @property
    def line_count(self) -> int | None:
        """Return the number of lines occupied by the function."""

        if self.start_line is None or self.end_line is None:
            return None

        return self.end_line - self.start_line + 1



@dataclass(slots=True)
class ParsedClass:
    """Represents a class found in a Python file."""

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
        """Return the number of lines occupied by the class."""

        if self.start_line is None or self.end_line is None:
            return None

        return self.end_line - self.start_line + 1



@dataclass(slots=True)
class ParseError:
    """Represents an error encountered while parsing a Python file."""

    message: str
    line_number: int | None = None
    column_number: int | None = None



@dataclass(slots=True)
class ParsedFile:
    """Represents the complete parsed result for one Python file."""

    path: Path
    module_name: str
    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[ParsedFunction] = field(default_factory=list)
    classes: list[ParsedClass] = field(default_factory=list)
    docstring: str | None = None
    line_count: int = 0
    parse_error: ParseError | None = None


    @property
    def function_count(self) -> int:
        """Return the number of top-level functions."""

        return len(self.functions)


    @property
    def class_count(self) -> int:
        """Return the number of classes."""

        return len(self.classes)

    @property
    def method_count(self) -> int:
        """Return the total number of methods across all classes."""

        return sum(len(parsed_class.methods) for parsed_class in self.classes)


    @property
    def was_parsed_successfully(self) -> bool:
        """Return whether the file was parsed without an error."""

        return self.parse_error is None

    