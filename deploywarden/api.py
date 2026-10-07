from fastapi import FastAPI, HTTPException, Response

from .config import Settings
from .service import ReleaseError, ReleaseService

app = FastAPI(title="DeployWarden", version="0.1.0")
service = ReleaseService(Settings.from_env())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict:
    return service.status()


@app.get("/audit")
def audit(limit: int = 50) -> list[dict]:
    return service.store.events(max(1, min(limit, 500)))


@app.get("/checkpoints")
def checkpoints() -> list[dict]:
    return [point.to_dict() for point in service.store.checkpoints()]


@app.get("/metrics")
def metrics() -> Response:
    return Response(service.metrics.render(), media_type="text/plain; version=0.0.4")


@app.post("/deploy/{version}")
def deploy(version: str, actor: str = "api") -> dict:
    try:
        return service.deploy(version, actor)
    except ReleaseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/rollback")
def rollback(checkpoint: str | None = None, actor: str = "api") -> dict:
    try:
        return service.rollback(checkpoint, actor)
    except ReleaseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
