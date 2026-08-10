from pydantic import BaseModel

from app.analyzer.service import (
    RepositoryAnalysisResult,
)

class AnalysisRequest(BaseModel):
    repository_path: str | None = None
    repository_url: str | None = None

class MetricsResponse(BaseModel):
    module_count: int
    dependency_count: int
    internal_dependency_count: int
    external_dependency_count: int
    unresolved_dependency_count: int
    isolated_module_count: int
    circular_dependency_count: int


class FindingResponse(BaseModel):
    finding_type: str
    severity: str
    message: str
    modules: list[str]


class ModuleResponse(BaseModel):
    module_name: str
    file_path: str


class EdgeResponse(BaseModel):
    source: str
    target: str
    dependency_type: str


class GraphResponse(BaseModel):
    nodes: list[ModuleResponse]
    edges: list[EdgeResponse]


class AnalysisResponse(BaseModel):
    metrics: MetricsResponse
    findings: list[FindingResponse]
    modules: list[ModuleResponse]
    graph: GraphResponse

    @classmethod
    def from_result(
        cls,
        result: RepositoryAnalysisResult,
    ) -> "AnalysisResponse":
        modules = [
            ModuleResponse(
                module_name=module.module_name,
                file_path=str(module.path),
            )
            for module in result.modules
        ]

        graph_nodes = [
            ModuleResponse(
                module_name=node.module_name,
                file_path=node.file_path,
            )
            for node in result.graph.nodes.values()
        ]

        graph_edges = [
            EdgeResponse(
                source=edge.source,
                target=edge.target,
                dependency_type=edge.dependency_type.value,
            )
            for edge in result.graph.edges
        ]

        findings = [
            FindingResponse(
                finding_type=finding.finding_type.value,
                severity=finding.severity.value,
                message=finding.message,
                modules=list(finding.modules),
            )
            for finding in result.findings
        ]

        return cls(
            metrics=MetricsResponse(
                module_count=result.metrics.module_count,
                dependency_count=result.metrics.dependency_count,
                internal_dependency_count=(
                    result.metrics.internal_dependency_count
                ),
                external_dependency_count=(
                    result.metrics.external_dependency_count
                ),
                unresolved_dependency_count=(
                    result.metrics.unresolved_dependency_count
                ),
                isolated_module_count=(
                    result.metrics.isolated_module_count
                ),
                circular_dependency_count=(
                    result.metrics.circular_dependency_count
                ),
            ),
            findings=findings,
            modules=modules,
            graph=GraphResponse(
                nodes=graph_nodes,
                edges=graph_edges,
            ),
        )