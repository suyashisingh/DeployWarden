from __future__ import annotations

import json

import typer

from .config import Settings
from .service import ReleaseError, ReleaseService

app = typer.Typer(help="DeployWarden: audited release and recovery automation.", no_args_is_help=True)


def service() -> ReleaseService:
    return ReleaseService(Settings.from_env())


@app.command()
def deploy(version: str, actor: str = typer.Option("cli", help="Audit identity")) -> None:
    """Deploy a version after creating a rollback checkpoint."""
    try:
        typer.echo(json.dumps(service().deploy(version, actor), indent=2))
    except ReleaseError as exc:
        typer.echo(f"release blocked: {exc}", err=True)
        raise typer.Exit(1)


@app.command()
def rollback(checkpoint: str | None = None, actor: str = typer.Option("cli", help="Audit identity")) -> None:
    """Recover to the latest or named checkpoint."""
    try:
        typer.echo(json.dumps(service().rollback(checkpoint, actor), indent=2))
    except ReleaseError as exc:
        typer.echo(f"rollback blocked: {exc}", err=True)
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show the current deployment state."""
    typer.echo(json.dumps(service().status(), indent=2))


@app.command("audit")
def audit(limit: int = typer.Option(20, min=1, max=500)) -> None:
    """Display recent immutable audit events."""
    typer.echo(json.dumps(service().store.events(limit), indent=2))


if __name__ == "__main__":
    app()
