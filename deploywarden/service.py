from __future__ import annotations

import os
import subprocess
import time
import uuid
from urllib.request import urlopen

from .config import Settings
from .metrics import Metrics
from .models import Checkpoint, DeploymentState, utc_now
from .store import StateStore


class ReleaseError(RuntimeError):
    pass


class ReleaseService:
    def __init__(self, settings: Settings, metrics: Metrics | None = None) -> None:
        self.settings = settings
        self.store = StateStore(settings.data_dir)
        self.metrics = metrics or Metrics()
        self.metrics.checkpoints.set(len(self.store.checkpoints()))

    def status(self) -> dict:
        return self.store.state().to_dict()

    def deploy(self, version: str, actor: str = "cli") -> dict:
        if not version.strip():
            raise ReleaseError("version is required")
        state = self.store.state()
        if state.operation != "idle":
            raise ReleaseError(f"cannot deploy while {state.operation} is active")
        if state.version == version:
            raise ReleaseError(f"version {version} is already deployed")
        checkpoint = self._create_checkpoint(state.version, "pre-deploy")
        self._set_operation("deploying")
        started = time.monotonic()
        try:
            self._run(self.settings.deploy_command, version, checkpoint.id)
            self._healthcheck()
            self.store.save_state(DeploymentState(version=version, updated_at=utc_now(), checkpoint=checkpoint.id))
            self.metrics.current_version.labels(version=version).set(1)
            self.metrics.releases.labels(action="deploy", outcome="success").inc()
            self._audit("deploy", "success", actor, version, checkpoint.id)
            return self.status()
        except Exception as exc:
            self.metrics.releases.labels(action="deploy", outcome="failure").inc()
            self._audit("deploy", "failure", actor, version, checkpoint.id, str(exc))
            raise ReleaseError(str(exc)) from exc
        finally:
            self.metrics.duration.labels(action="deploy").observe(time.monotonic() - started)
            self._set_operation("idle")

    def rollback(self, checkpoint_id: str | None = None, actor: str = "cli") -> dict:
        state = self.store.state()
        if state.operation != "idle":
            raise ReleaseError(f"cannot roll back while {state.operation} is active")
        checkpoints = self.store.checkpoints()
        checkpoint = next((x for x in checkpoints if x.id == checkpoint_id), None) if checkpoint_id else (checkpoints[-1] if checkpoints else None)
        if checkpoint is None:
            raise ReleaseError("no matching rollback checkpoint")
        self._set_operation("rolling_back")
        started = time.monotonic()
        try:
            self._run(self.settings.rollback_command, checkpoint.version or "", checkpoint.id)
            self._healthcheck()
            self.store.save_state(DeploymentState(version=checkpoint.version, updated_at=utc_now(), checkpoint=checkpoint.id))
            self.metrics.releases.labels(action="rollback", outcome="success").inc()
            self._audit("rollback", "success", actor, checkpoint.version, checkpoint.id)
            return self.status()
        except Exception as exc:
            self.metrics.releases.labels(action="rollback", outcome="failure").inc()
            self._audit("rollback", "failure", actor, checkpoint.version, checkpoint.id, str(exc))
            raise ReleaseError(str(exc)) from exc
        finally:
            self.metrics.duration.labels(action="rollback").observe(time.monotonic() - started)
            self._set_operation("idle")

    def _create_checkpoint(self, version: str | None, reason: str) -> Checkpoint:
        checkpoint = Checkpoint(id=f"cp-{uuid.uuid4().hex[:12]}", version=version, created_at=utc_now(), reason=reason)
        points = self.store.checkpoints()
        points.append(checkpoint)
        self.store.save_checkpoints(points)
        self.metrics.checkpoints.set(len(points))
        self._audit("checkpoint", "success", "system", version, checkpoint.id)
        return checkpoint

    def _set_operation(self, operation: str) -> None:
        state = self.store.state()
        state.operation = operation
        self.store.save_state(state)
        self.metrics.in_progress.set(0 if operation == "idle" else 1)

    def _run(self, command: str | None, version: str, checkpoint: str) -> None:
        if not command:
            return
        environment = {**os.environ, "DEPLOYWARDEN_VERSION": version, "DEPLOYWARDEN_CHECKPOINT": checkpoint}
        subprocess.run(command, shell=True, check=True, env=environment, timeout=600)

    def _healthcheck(self) -> None:
        if not self.settings.healthcheck_url:
            return
        with urlopen(self.settings.healthcheck_url, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise ReleaseError(f"health check returned HTTP {response.status}")

    def _audit(self, action: str, outcome: str, actor: str, version: str | None, checkpoint: str | None, detail: str | None = None) -> None:
        self.store.audit({"timestamp": utc_now(), "action": action, "outcome": outcome, "actor": actor, "version": version, "checkpoint": checkpoint, "detail": detail})
