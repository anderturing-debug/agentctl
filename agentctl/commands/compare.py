"""Compare command — run same prompt across multiple models."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentctl.config import AgentctlConfig
from agentctl.providers import Message, get_provider

import agentctl.providers.ollama  # noqa: F401
import agentctl.providers.anthropic_provider  # noqa: F401
import agentctl.providers.openai_provider  # noqa: F401


@click.command()
@click.argument("prompt")
@click.option("--models", "-m", required=True, help="Comma-separated list of provider:model pairs")
@click.option("--system", "-s", help="System prompt")
def compare(prompt: str, models: str, system: str | None):
    """Compare outputs from multiple models.

    Example:

        agentctl compare "Explain TCP" --models anthropic:claude-sonnet,openai:gpt-4o,ollama:llama3.1:8b
    """
    asyncio.run(_compare(prompt, models, system))


async def _compare(prompt: str, models_str: str, system: str | None):
    console = Console()
    cfg = AgentctlConfig.load()

    model_specs = []
    for spec in models_str.split(","):
        spec = spec.strip()
        if ":" in spec:
            parts = spec.split(":", 1)
            model_specs.append((parts[0], parts[1]))
        else:
            # Use default provider
            model_specs.append((cfg.defaults.provider, spec))

    messages = []
    if system:
        messages.append(Message(role="system", content=system))
    messages.append(Message(role="user", content=prompt))

    console.print(f"\n[bold]Prompt:[/bold] {prompt}\n")

    results = []

    for pname, model in model_specs:
        try:
            pcfg = cfg.providers.get(pname)
            provider_cls = get_provider(pname)

            init_kwargs = {}
            if pcfg:
                if pcfg.api_key:
                    init_kwargs["api_key"] = pcfg.api_key
                if pcfg.endpoint:
                    init_kwargs["endpoint"] = pcfg.endpoint

            instance = provider_cls(**init_kwargs)

            with console.status(f"[cyan]Querying {pname}:{model}...[/cyan]"):
                response = await instance.complete(messages, model=model)

            results.append((pname, model, response))

            console.print(
                Panel(
                    response.content,
                    title=f"[bold cyan]{pname}:{model}[/bold cyan]",
                    subtitle=f"[dim]{response.input_tokens}→{response.output_tokens} tokens | ${response.cost:.4f} | {response.latency_ms:.0f}ms[/dim]",
                )
            )
        except Exception as e:
            console.print(f"[red]Error with {pname}:{model}: {e}[/red]")

    # Summary table
    if len(results) > 1:
        table = Table(title="Comparison Summary")
        table.add_column("Model", style="cyan")
        table.add_column("Output Tokens", justify="right")
        table.add_column("Cost", justify="right", style="green")
        table.add_column("Latency", justify="right")

        for pname, model, resp in results:
            table.add_row(
                f"{pname}:{model}",
                str(resp.output_tokens),
                f"${resp.cost:.4f}",
                f"{resp.latency_ms:.0f}ms",
            )

        console.print(table)
