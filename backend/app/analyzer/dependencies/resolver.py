"""Resolve dependency targets against imports and local definitions."""

import ast

from app.analyzer.parsing.models import (
    ImportInfo,
    ParsedClass,
    ParsedFunction,
)

from .models import Dependency, ResolvedDependency


class DependencyResolver:
    """Resolve raw dependency names to imported or local components."""

    def resolve_dependencies(
        self,
        *,
        dependencies: list[Dependency],
        imports: list[ImportInfo],
        functions: list[ParsedFunction],
        classes: list[ParsedClass],
    ) -> list[ResolvedDependency]:
        """Resolve all dependencies in a parsed module."""

        import_map = self._build_import_map(imports)

        local_names = {
            function.name
            for function in functions
        }

        local_names.update(
            parsed_class.name
            for parsed_class in classes
        )

        instance_attribute_map = self._build_instance_attribute_map(
            classes
        )

        return [
            self._resolve_dependency(
                dependency=dependency,
                import_map=import_map,
                local_names=local_names,
                instance_attribute_map=instance_attribute_map,
            )
            for dependency in dependencies
        ]

    def _resolve_dependency(
        self,
        *,
        dependency: Dependency,
        import_map: dict[str, str],
        local_names: set[str],
        instance_attribute_map: dict[tuple[str, str], str],
    ) -> ResolvedDependency:
        """Resolve one raw dependency."""

        instance_target = self._resolve_instance_target(
            dependency=dependency,
            instance_attribute_map=instance_attribute_map,
        )

        if instance_target is not None:
            root_name = instance_target.split(".", maxsplit=1)[0]

            if root_name in import_map:
                target_category = "imported"
                imported_from = import_map[root_name]
            elif root_name in local_names:
                target_category = "local"
                imported_from = None
            else:
                target_category = "unresolved"
                imported_from = None

            return ResolvedDependency(
                source=dependency.source,
                target=instance_target,
                dependency_type=dependency.dependency_type,
                target_category=target_category,
                imported_from=imported_from,
                line_number=dependency.line_number,
            )

        root_name = dependency.target.split(".", maxsplit=1)[0]

        if root_name in import_map:
            return ResolvedDependency(
                source=dependency.source,
                target=dependency.target,
                dependency_type=dependency.dependency_type,
                target_category="imported",
                imported_from=import_map[root_name],
                line_number=dependency.line_number,
            )

        if root_name in local_names:
            return ResolvedDependency(
                source=dependency.source,
                target=dependency.target,
                dependency_type=dependency.dependency_type,
                target_category="local",
                imported_from=None,
                line_number=dependency.line_number,
            )

        return ResolvedDependency(
            source=dependency.source,
            target=dependency.target,
            dependency_type=dependency.dependency_type,
            target_category="unresolved",
            imported_from=None,
            line_number=dependency.line_number,
        )

    def _resolve_instance_target(
        self,
        *,
        dependency: Dependency,
        instance_attribute_map: dict[tuple[str, str], str],
    ) -> str | None:
        """Resolve a self-attribute call to its constructed type."""

        if not dependency.target.startswith("self."):
            return None

        target_parts = dependency.target.split(".")

        # A resolvable instance call needs at least:
        # self.attribute.method
        if len(target_parts) < 3:
            return None

        source_class = dependency.source.split(".", maxsplit=1)[0]

        attribute_name = ".".join(target_parts[:2])
        remaining_path = ".".join(target_parts[2:])

        constructed_type = instance_attribute_map.get(
            (
                source_class,
                attribute_name,
            )
        )

        if constructed_type is None:
            return None

        return f"{constructed_type}.{remaining_path}"

    def _build_instance_attribute_map(
        self,
        classes: list[ParsedClass],
    ) -> dict[tuple[str, str], str]:
        """Map class instance attributes to constructed types."""

        attribute_map: dict[tuple[str, str], str] = {}

        for parsed_class in classes:
            constructor = next(
                (
                    method
                    for method in parsed_class.methods
                    if method.name == "__init__"
                ),
                None,
            )

            if constructor is None:
                continue

            for assignment in constructor.assignments:
                if not assignment.is_instance_attribute:
                    continue

                constructor_name = self._get_constructor_name(
                    assignment.value
                )

                if constructor_name is None:
                    continue

                attribute_map[
                    (
                        parsed_class.name,
                        assignment.target,
                    )
                ] = constructor_name

        return attribute_map

    def _get_constructor_name(
        self,
        value: str | None,
    ) -> str | None:
        """Extract a constructor name from an assignment value."""

        if value is None:
            return None

        try:
            expression = ast.parse(
                value,
                mode="eval",
            ).body
        except SyntaxError:
            return None

        if not isinstance(expression, ast.Call):
            return None

        return self._get_callable_name(expression.func)

    def _get_callable_name(
        self,
        node: ast.AST,
    ) -> str | None:
        """Convert a callable AST node into a readable name."""

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parent_name = self._get_callable_name(node.value)

            if parent_name is None:
                return node.attr

            return f"{parent_name}.{node.attr}"

        return None

    def _build_import_map(
        self,
        imports: list[ImportInfo],
    ) -> dict[str, str]:
        """Map names available in a module to their import sources."""

        import_map: dict[str, str] = {}

        for imported_item in imports:
            if imported_item.is_from_import:
                self._add_from_import(
                    import_map=import_map,
                    imported_item=imported_item,
                )
            else:
                self._add_regular_import(
                    import_map=import_map,
                    imported_item=imported_item,
                )

        return import_map

    def _add_regular_import(
        self,
        *,
        import_map: dict[str, str],
        imported_item: ImportInfo,
    ) -> None:
        """Add a regular import to the import map."""

        available_name = (
            imported_item.alias
            or imported_item.module.split(".", maxsplit=1)[0]
        )

        import_map[available_name] = imported_item.module

    def _add_from_import(
        self,
        *,
        import_map: dict[str, str],
        imported_item: ImportInfo,
    ) -> None:
        """Add names from a from-import statement."""

        for imported_name in imported_item.names:
            available_name = imported_item.alias or imported_name

            if imported_item.module:
                full_source = (
                    f"{imported_item.module}.{imported_name}"
                )
            else:
                full_source = imported_name

            import_map[available_name] = full_source