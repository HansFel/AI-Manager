from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .models import EntryKind, ModelsFile
from .registry import RegistryStore, fingerprint

app = typer.Typer(no_args_is_help=True)
console = Console()


def store(path: Path) -> RegistryStore:
    return RegistryStore(path)


@app.command()
def init(
    registry: Path = typer.Option(Path(".ai-management/registry.json"), help="Registry path."),
) -> None:
    """Create the local registry."""
    created = store(registry).init()
    if created:
        console.print(f"[green]Created registry:[/] {registry}")
    else:
        console.print(f"[yellow]Registry already exists:[/] {registry}")


@app.command()
def models(
    config: Path = typer.Option(Path("configs/models.example.yaml"), help="Models YAML."),
) -> None:
    """Show configured models and roles."""
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    parsed = ModelsFile.model_validate(data)

    table = Table(title="Configured AI models")
    table.add_column("ID")
    table.add_column("Provider")
    table.add_column("Roles")
    table.add_column("Priority", justify="right")
    table.add_column("Enabled")

    for model in sorted(parsed.models, key=lambda item: item.priority, reverse=True):
        table.add_row(
            model.id,
            model.provider,
            ", ".join(model.roles),
            str(model.priority),
            "yes" if model.enabled else "no",
        )
    console.print(table)


@app.command("register-skill")
def register_skill(
    name: str,
    description: str = typer.Option("", "--description", "-d"),
    tag: list[str] = typer.Option([], "--tag", "-t"),
    registry: Path = typer.Option(Path(".ai-management/registry.json")),
) -> None:
    """Register a reusable skill and show possible overlaps."""
    entry, matches = store(registry).add_entry(EntryKind.SKILL, name, description, tag)
    console.print(f"[green]Registered skill:[/] {entry.name}")
    _print_matches(matches)


@app.command("register-agent")
def register_agent(
    name: str,
    description: str = typer.Option("", "--description", "-d"),
    tag: list[str] = typer.Option([], "--tag", "-t"),
    registry: Path = typer.Option(Path(".ai-management/registry.json")),
) -> None:
    """Register an agent and show possible overlaps."""
    entry, matches = store(registry).add_entry(EntryKind.AGENT, name, description, tag)
    console.print(f"[green]Registered agent:[/] {entry.name}")
    _print_matches(matches)


@app.command()
def check(
    name: str,
    description: str = typer.Option("", "--description", "-d"),
    kind: EntryKind = typer.Option(EntryKind.SKILL),
    registry: Path = typer.Option(Path(".ai-management/registry.json")),
) -> None:
    """Check whether an agent or skill already exists before creating it."""
    fp = fingerprint(name, description)
    matches = store(registry).find_similar(fp, kind=kind)
    if not matches:
        console.print("[green]No likely duplicate found.[/]")
        return
    _print_matches(matches)


@app.command()
def duplicates(
    threshold: float = typer.Option(0.78, min=0.1, max=1.0),
    registry: Path = typer.Option(Path(".ai-management/registry.json")),
) -> None:
    """Show likely duplicate registry entries."""
    groups = store(registry).duplicate_groups(threshold=threshold)
    if not groups:
        console.print("[green]No duplicate groups found.[/]")
        return

    for index, group in enumerate(groups, start=1):
        table = Table(title=f"Duplicate group {index}")
        table.add_column("Kind")
        table.add_column("Name")
        table.add_column("Score", justify="right")
        table.add_column("Fingerprint")
        for entry, score in group:
            table.add_row(entry.kind, entry.name, f"{score:.2f}", entry.fingerprint)
        console.print(table)


def _print_matches(matches) -> None:
    if not matches:
        console.print("[green]No likely overlap found.[/]")
        return

    table = Table(title="Possible overlaps")
    table.add_column("Kind")
    table.add_column("Name")
    table.add_column("Score", justify="right")
    table.add_column("Fingerprint")
    for entry, score in matches:
        table.add_row(entry.kind, entry.name, f"{score:.2f}", entry.fingerprint)
    console.print(table)


if __name__ == "__main__":
    app()
