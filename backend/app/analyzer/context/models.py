from dataclasses import dataclass, field


@dataclass(slots=True)
class ArchitectureContext:
    file_count: int = 0
    function_count: int = 0
    class_count: int = 0
    method_count: int = 0

    modules: list[str] = field(default_factory=list)

    internal_dependencies: list[str] = field(default_factory=list)
    external_dependencies: list[str] = field(default_factory=list)

    highly_connected_modules: list[str] = field(default_factory=list)
    circular_dependencies: list[str] = field(default_factory=list)