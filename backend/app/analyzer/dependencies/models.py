"""Models representing architectural dependencies."""

from dataclasses import dataclass


@dataclass
class Dependency:
    """A relationship between two code components."""

    source: str
    target: str
    dependency_type: str
    line_number: int | None = None