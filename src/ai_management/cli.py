from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .models import EntryKind, ModelsFile
from .projects import ProjectStore
from .registry import RegistryStore, fingerprint
from .security import UserStore

app = typer.Typer(no_args_is_help=True)
console = Console()


def store(path: Path) -> RegistryStore:
    return RegistryStore(path)


def project_store(path: Path) -> ProjectStore:
    return ProjectStore(path)


@app.command()
def init(
    registry: Path = typer.Option(Path(".ai-management/registry.json"), help="Registry path."),
    projects: Path = typer.Option(Path(".ai-management/projects.json"), help="Projects catalog path."),
) -> None:
    """Create the local registry and project catalog."""
    created = store(registry).init()
    projects_created = project_store(projects).init()
    if created:
        console.print(f"[green]Created registry:[/] {registry}")
    else:
        console.print(f"[yellow]Registry already exists:[/] {registry}")
    if projects_created:
        console.print(f"[green]Created projects catalog:[/] {projects}")
    else:
        console.print(f"[yellow]Projects catalog already exists:[/] {projects}")


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


@app.command("register-project")
def register_project(
    name: str,
    repo_url: str = typer.Option("", "--repo-url"),
    local_path: str = typer.Option("", "--local-path"),
    description: str = typer.Option("", "--description", "-d"),
    tag: list[str] = typer.Option([], "--tag", "-t"),
    owner: str = typer.Option("", "--owner"),
    projects: Path = typer.Option(Path(".ai-management/projects.json")),
) -> None:
    """Register a repository or project."""
    entry = project_store(projects).add_project(
        name=name,
        repo_url=repo_url,
        local_path=local_path,
        description=description,
        tags=tag,
        owner=owner,
    )
    console.print(f"[green]Registered project:[/] {entry.name}")


@app.command("register-commonality")
def register_commonality(
    title: str,
    category: str = typer.Option("shared", "--category", "-c"),
    description: str = typer.Option("", "--description", "-d"),
    project_id: list[str] = typer.Option([], "--project-id"),
    tag: list[str] = typer.Option([], "--tag", "-t"),
    projects: Path = typer.Option(Path(".ai-management/projects.json")),
) -> None:
    """Register a shared concern across repositories."""
    entry = project_store(projects).add_commonality(
        title=title,
        category=category,
        description=description,
        project_ids=project_id,
        tags=tag,
    )
    console.print(f"[green]Registered commonality:[/] {entry.title}")


@app.command("projects")
def projects_list(
    projects: Path = typer.Option(Path(".ai-management/projects.json")),
) -> None:
    """Show registered projects and shared concerns."""
    catalog = project_store(projects).load()
    table = Table(title="Projects")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Repo")
    table.add_column("Tags")
    for project in catalog.projects:
        table.add_row(project.id[:8], project.name, project.repo_url, ", ".join(project.tags))
    console.print(table)

    shared = Table(title="Commonalities")
    shared.add_column("ID")
    shared.add_column("Title")
    shared.add_column("Category")
    shared.add_column("Projects")
    names = {project.id: project.name for project in catalog.projects}
    for item in catalog.commonalities:
        shared.add_row(
            item.id[:8],
            item.title,
            item.category,
            ", ".join(names.get(project_id, project_id[:8]) for project_id in item.project_ids),
        )
    console.print(shared)


@app.command("create-user")
def create_user(
    username: str = typer.Option("admin", "--username", "-u"),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
    ),
    role: str = typer.Option("admin", "--role", "-r"),
    users: Path = typer.Option(Path(".ai-management/users.local.json")),
) -> None:
    """Create or update a local web user."""
    store = UserStore(users)
    created = store.upsert_user(username=username, password=password, role=role)
    if created:
        console.print(f"[green]Created user:[/] {username}")
    else:
        console.print(f"[yellow]Updated user:[/] {username}")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the local web management UI."""
    import uvicorn

    console.print(f"[green]Starting AI Management Hub:[/] http://{host}:{port}")
    uvicorn.run("ai_management.web:app", host=host, port=port, reload=reload)


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
