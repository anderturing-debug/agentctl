"""Logs command — stream session logs."""

import json
import time

import click
from rich.console import Console

from agentctl.config import SESSIONS_DIR


@click.command()
@click.argument("session_name")
@click.option("--follow", "-f", is_flag=True, help="Follow logs in real-time")
@click.option("--last", "-n", type=int, default=20, help="Number of recent messages")
def logs(session_name: str, follow: bool, last: int):
    """Stream logs from a session.

    Example:

        agentctl logs my-agent --follow
    """
    console = Console()
    messages_file = SESSIONS_DIR / session_name / "messages.jsonl"

    if not messages_file.exists():
        console.print(f"[red]Session '{session_name}' not found.[/red]")
        return

    # Print last N messages
    lines = messages_file.read_text().strip().split("\n")
    lines = [l for l in lines if l.strip()]
    recent = lines[-last:]

    for line in recent:
        _print_message(console, json.loads(line))

    if not follow:
        return

    # Follow mode — tail the file
    console.print("\n[dim]Following... (Ctrl+C to stop)[/dim]\n")
    seen = len(lines)

    try:
        while True:
            current_lines = messages_file.read_text().strip().split("\n")
            current_lines = [l for l in current_lines if l.strip()]

            if len(current_lines) > seen:
                for line in current_lines[seen:]:
                    _print_message(console, json.loads(line))
                seen = len(current_lines)

            time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped following.[/dim]")


def _print_message(console: Console, msg: dict):
    role = msg.get("role", "?")
    content = msg.get("content", "")
    ts = msg.get("timestamp", "")

    colors = {"user": "cyan", "assistant": "green", "system": "yellow"}
    color = colors.get(role, "white")

    prefix = f"[dim]{ts}[/dim] " if ts else ""
    console.print(f"{prefix}[bold {color}]{role}:[/bold {color}] {content}")
