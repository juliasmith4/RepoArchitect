"""Models representing architectural dependencies."""

from dataclasses import dataclass


@dataclass
class Dependency:
    """A relationship between two code components."""

    source: str
    target: str
    dependency_type: str
    line_number: int | None = None


@dataclass
class ResolvedDependency:
    """A dependency with import resolution information."""

    source: str
    target: str
    dependency_type: str
    target_category: str
    imported_from: str | None
    line_number: int | None = None