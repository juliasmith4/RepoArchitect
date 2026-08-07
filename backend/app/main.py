from fastapi import FastAPI

from app.api.routes.analysis import router as analysis_router


app = FastAPI(
    title="RepoArchitect API",
    version="0.1.0",
)


app.include_router(
    analysis_router,
    prefix="/analysis",
    tags=["analysis"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}