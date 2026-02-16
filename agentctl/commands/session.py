"""Session management commands."""

import json
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from agentctl.config import SESSIONS_DIR


@click.group()
def session():
    """Manage conversation sessions."""
    pass


@session.command("list")
def session_list():
    """List all saved sessions."""
    console = Console()
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    sessions = sorted(SESSIONS_DIR.iterdir()) if SESSIONS_DIR.exists() else []

    if not sessions:
        console.print("[dim]No sessions found. Start one with: agentctl session new[/dim]")
        return

    table = Table(title="Sessions")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Messages")
    table.add_column("Created", style="dim")
    table.add_column("Last Active", style="dim")

    for session_dir in sessions:
        if not session_dir.is_dir():
            continue
        meta_file = session_dir / "session.json"
        if not meta_file.exists():
            continue

        meta = json.loads(meta_file.read_text())
        messages_file = session_dir / "messages.jsonl"
        msg_count = sum(1 for _ in open(messages_file)) if messages_file.exists() else 0

        table.add_row(
            meta.get("name", session_dir.name),
            meta.get("model", "?"),
            str(msg_count),
            meta.get("created", "?"),
            meta.get("last_active", "?"),
        )

    console.print(table)


@session.command("new")
@click.option("--name", "-n", required=True, help="Session name")
@click.option("--model", "-m", help="Model to use")
@click.option("--system", "-s", help="System prompt")
def session_new(name: str, model: str | None, system: str | None):
    """Create a new conversation session."""
    session_dir = SESSIONS_DIR / name
    session_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "name": name,
        "model": model,
        "system": system,
        "created": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
    }

    (session_dir / "session.json").write_text(json.dumps(meta, indent=2))
    (session_dir / "messages.jsonl").touch()

    click.echo(f"✓ Session '{name}' created.")
    if model:
        click.echo(f"  Model: {model}")


@session.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure?")
def session_delete(name: str):
    """Delete a session."""
    import shutil

    session_dir = SESSIONS_DIR / name
    if not session_dir.exists():
        click.echo(f"Session '{name}' not found.")
        return

    shutil.rmtree(session_dir)
    click.echo(f"✓ Session '{name}' deleted.")


@session.command("show")
@click.argument("name")
@click.option("--last", "-n", type=int, default=10, help="Show last N messages")
def session_show(name: str, last: int):
    """Show messages from a session."""
    console = Console()
    session_dir = SESSIONS_DIR / name
    messages_file = session_dir / "messages.jsonl"

    if not messages_file.exists():
        console.print(f"[red]Session '{name}' not found.[/red]")
        return

    lines = messages_file.read_text().strip().split("\n")
    lines = [l for l in lines if l.strip()]
    lines = lines[-last:]

    for line in lines:
        msg = json.loads(line)
        role = msg.get("role", "?")
        content = msg.get("content", "")

        if role == "user":
            console.print(f"\n[bold cyan]You:[/bold cyan] {content}")
        elif role == "assistant":
            console.print(f"\n[bold green]Agent:[/bold green] {content}")
        elif role == "system":
            console.print(f"\n[bold yellow]System:[/bold yellow] {content}")
