from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deploywarden.api import app
from deploywarden.config import Settings
from deploywarden.metrics import Metrics
from deploywarden.service import ReleaseError, ReleaseService


def build_service(tmp_path: Path) -> ReleaseService:
    return ReleaseService(Settings(tmp_path, None, None, None), Metrics())


def test_deploy_creates_checkpoint_and_audit_record(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    result = service.deploy("2.0.0", actor="test-user")

    assert result["version"] == "2.0.0"
    assert result["operation"] == "idle"
    assert len(service.store.checkpoints()) == 1
    events = service.store.events()
    assert events[0]["action"] == "deploy"
    assert events[0]["actor"] == "test-user"


def test_rollback_restores_checkpointed_version(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    service.deploy("1.0.0")
    service.deploy("2.0.0")

    result = service.rollback()

    assert result["version"] == "1.0.0"
    assert service.store.events()[0]["action"] == "rollback"


def test_duplicate_version_is_blocked(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    service.deploy("1.0.0")
    with pytest.raises(ReleaseError, match="already deployed"):
        service.deploy("1.0.0")


def test_api_exposes_operations_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
