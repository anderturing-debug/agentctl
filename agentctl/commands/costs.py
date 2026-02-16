"""Cost tracking commands."""

import json
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from agentctl.config import COSTS_DIR


def _load_costs(month: str | None = None) -> list[dict]:
    """Load cost records for a given month."""
    COSTS_DIR.mkdir(parents=True, exist_ok=True)
    month = month or datetime.now().strftime("%Y-%m")
    costs_file = COSTS_DIR / f"{month}.jsonl"

    if not costs_file.exists():
        return []

    records = []
    for line in costs_file.read_text().strip().split("\n"):
        if line.strip():
            records.append(json.loads(line))
    return records


def record_cost(model: str, provider: str, input_tokens: int, output_tokens: int, cost: float):
    """Record a cost entry."""
    COSTS_DIR.mkdir(parents=True, exist_ok=True)
    month = datetime.now().strftime("%Y-%m")
    costs_file = COSTS_DIR / f"{month}.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "provider": provider,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }

    with open(costs_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


@click.command()
@click.option("--today", is_flag=True, help="Show today's costs only")
@click.option("--this-month", "this_month", is_flag=True, help="Show this month's costs")
@click.option("--month", help="Show costs for a specific month (YYYY-MM)")
@click.option("--by-model", "by_model", is_flag=True, help="Group by model")
def costs(today: bool, this_month: bool, month: str | None, by_model: bool):
    """View cost tracking data."""
    console = Console()

    target_month = month or datetime.now().strftime("%Y-%m")
    records = _load_costs(target_month)

    if today:
        today_str = datetime.now().strftime("%Y-%m-%d")
        records = [r for r in records if r["timestamp"].startswith(today_str)]

    if not records:
        console.print("[dim]No cost data found for this period.[/dim]")
        return

    if by_model:
        # Group by model
        model_stats: dict[str, dict] = {}
        for r in records:
            m = r["model"]
            if m not in model_stats:
                model_stats[m] = {"calls": 0, "input": 0, "output": 0, "cost": 0.0}
            model_stats[m]["calls"] += 1
            model_stats[m]["input"] += r["input_tokens"]
            model_stats[m]["output"] += r["output_tokens"]
            model_stats[m]["cost"] += r["cost"]

        table = Table(title=f"Costs by Model ({target_month})")
        table.add_column("Model", style="cyan")
        table.add_column("Calls", justify="right")
        table.add_column("Tokens (in/out)", justify="right")
        table.add_column("Cost", justify="right", style="green")

        total_cost = 0.0
        for m, stats in sorted(model_stats.items()):
            tokens = f"{stats['input']:,} / {stats['output']:,}"
            table.add_row(m, str(stats["calls"]), tokens, f"${stats['cost']:.4f}")
            total_cost += stats["cost"]

        table.add_section()
        table.add_row("[bold]Total[/bold]", str(len(records)), "", f"[bold]${total_cost:.4f}[/bold]")
        console.print(table)
    else:
        total_cost = sum(r["cost"] for r in records)
        total_calls = len(records)
        total_input = sum(r["input_tokens"] for r in records)
        total_output = sum(r["output_tokens"] for r in records)

        console.print(f"\n[bold]Period:[/bold] {target_month}")
        console.print(f"[bold]Total calls:[/bold] {total_calls}")
        console.print(f"[bold]Total tokens:[/bold] {total_input:,} in / {total_output:,} out")
        console.print(f"[bold]Total cost:[/bold] ${total_cost:.4f}")
