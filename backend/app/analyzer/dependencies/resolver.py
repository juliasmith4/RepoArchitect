"""Resolve dependency targets against imports and local definitions."""

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

        return [
            self._resolve_dependency(
                dependency=dependency,
                import_map=import_map,
                local_names=local_names,
            )
            for dependency in dependencies
        ]

    def _resolve_dependency(
        self,
        *,
        dependency: Dependency,
        import_map: dict[str, str],
        local_names: set[str],
    ) -> ResolvedDependency:
        """Resolve one raw dependency."""

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