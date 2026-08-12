from app.analyzer.graph.analysis import DependencyGraphAnalyzer
from app.analyzer.graph.dependency_graph import DependencyGraph
from app.analyzer.parsing.models import ParsedModule

from .models import ArchitectureContext


class ArchitectureContextBuilder:
    """Build repository-level architecture context."""

    def build(
        self,
        parsed_modules: list[ParsedModule],
        dependency_graph: DependencyGraph | None = None,
    ) -> ArchitectureContext:
        context = ArchitectureContext()

        self._add_module_information(
            context=context,
            parsed_modules=parsed_modules,
        )

        if dependency_graph is not None:
            self._add_dependencies(
                context=context,
                dependency_graph=dependency_graph,
            )

            self._add_graph_analysis(
                context=context,
                dependency_graph=dependency_graph,
            )

        return context

    def _add_module_information(
        self,
        context: ArchitectureContext,
        parsed_modules: list[ParsedModule],
    ) -> None:
        for module in parsed_modules:
            if not module.was_parsed_successfully:
                continue

            context.file_count += 1
            context.function_count += module.function_count
            context.class_count += module.class_count
            context.method_count += module.method_count

            context.modules.append(module.module_name)

    def _add_dependencies(
        self,
        context: ArchitectureContext,
        dependency_graph: DependencyGraph,
    ) -> None:
        for edge in dependency_graph.internal_edges():
            context.internal_dependencies.append(
                f"{edge.source} -> {edge.target}"
            )

        for edge in dependency_graph.external_edges():
            context.external_dependencies.append(
                f"{edge.source} -> {edge.target}"
            )

        for edge in dependency_graph.unresolved_edges():
            context.unresolved_dependencies.append(
                f"{edge.source} -> {edge.target}"
            )

    def _add_graph_analysis(
        self,
        context: ArchitectureContext,
        dependency_graph: DependencyGraph,
    ) -> None:
        analyzer = DependencyGraphAnalyzer(dependency_graph)

        context.most_depended_on_modules = [
            metric.module_name
            for metric in analyzer.most_depended_on_modules()
            if metric.incoming_dependencies > 0
        ]

        context.isolated_modules = analyzer.isolated_modules()

        context.circular_dependencies = analyzer.find_cycles()