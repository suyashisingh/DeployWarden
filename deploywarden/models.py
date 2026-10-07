from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DeploymentState:
    version: str | None = None
    operation: str = "idle"
    updated_at: str | None = None
    checkpoint: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Checkpoint:
    id: str
    version: str | None
    created_at: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)
