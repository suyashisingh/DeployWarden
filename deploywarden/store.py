from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from .models import Checkpoint, DeploymentState


class StateStore:
    """Small durable store designed for one deployment controller instance."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.state_path = data_dir / "state.json"
        self.audit_path = data_dir / "audit.jsonl"
        self.checkpoint_path = data_dir / "checkpoints.json"
        self._lock = Lock()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def state(self) -> DeploymentState:
        if not self.state_path.exists():
            return DeploymentState()
        return DeploymentState(**json.loads(self.state_path.read_text(encoding="utf-8")))

    def save_state(self, state: DeploymentState) -> None:
        self._write_json(self.state_path, state.to_dict())

    def checkpoints(self) -> list[Checkpoint]:
        if not self.checkpoint_path.exists():
            return []
        return [Checkpoint(**item) for item in json.loads(self.checkpoint_path.read_text(encoding="utf-8"))]

    def save_checkpoints(self, checkpoints: list[Checkpoint]) -> None:
        self._write_json(self.checkpoint_path, [item.to_dict() for item in checkpoints])

    def audit(self, event: dict[str, Any]) -> None:
        with self._lock, self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    def events(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.audit_path.exists():
            return []
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:]][::-1]

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(path)
