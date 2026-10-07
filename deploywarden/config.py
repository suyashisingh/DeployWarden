from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    deploy_command: str | None
    rollback_command: str | None
    healthcheck_url: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            data_dir=Path(os.getenv("DEPLOYWARDEN_DATA_DIR", ".deploywarden")),
            deploy_command=os.getenv("DEPLOY_COMMAND"),
            rollback_command=os.getenv("ROLLBACK_COMMAND"),
            healthcheck_url=os.getenv("HEALTHCHECK_URL"),
        )
