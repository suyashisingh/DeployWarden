# DeployWarden

DeployWarden is a safety-first release automation CLI with an optional FastAPI operations API. It replaces ad-hoc deployment steps with audited, checkpointed release and rollback workflows.

## Features

- `deploywarden deploy <version>` creates a backup checkpoint, runs configured health checks, promotes the release, and records every event in an append-only JSONL audit log.
- `deploywarden rollback [checkpoint]` restores the latest (or named) checkpoint in one command.
- Deployment state is guarded by a lock and validated transitions; unsafe operations fail before making a change.
- Prometheus metrics expose deployment outcomes, duration, current release, active operation, and checkpoint count.
- FastAPI exposes health, deployment status, audit history, checkpoints, and Prometheus metrics.
- GitHub Actions supports manual releases plus a scheduled deployment-health audit; failures automatically invoke rollback when a checkpoint was created.

## Quick start

```bash
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -e ".[dev]"
deploywarden deploy 1.2.0 --actor alice
deploywarden status
deploywarden rollback --actor alice
uvicorn deploywarden.api:app --host 0.0.0.0 --port 8000
```

By default, DeployWarden stores local state under `.deploywarden/`. Set `DEPLOYWARDEN_DATA_DIR` to choose a persistent volume location.

## Production configuration

Set `DEPLOY_COMMAND` and `ROLLBACK_COMMAND` to run your release platform commands. Each command receives `DEPLOYWARDEN_VERSION` and `DEPLOYWARDEN_CHECKPOINT` environment variables. Set `HEALTHCHECK_URL` to require an HTTP 2xx health check after deployment.

```bash
DEPLOY_COMMAND="./scripts/release.sh" ROLLBACK_COMMAND="./scripts/restore.sh" HEALTHCHECK_URL="https://service.example/health" deploywarden deploy 1.2.0
```

## API

- `GET /health` — process health
- `GET /status` — deployed version and operation state
- `GET /audit` — recent immutable audit events
- `GET /checkpoints` — recovery points
- `GET /metrics` — Prometheus scrape endpoint

Run the test suite with `pytest`.
