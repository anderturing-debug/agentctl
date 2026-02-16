"""Models command — list available models."""

import click
from rich.console import Console
from rich.table import Table

from agentctl.config import AgentctlConfig
from agentctl.providers import get_provider, list_providers

# Import providers to trigger registration
import agentctl.providers.ollama  # noqa: F401
import agentctl.providers.anthropic_provider  # noqa: F401
import agentctl.providers.openai_provider  # noqa: F401


@click.command()
@click.option("--provider", "-p", help="Filter by provider")
def models(provider: str | None):
    """List available models across all configured providers."""
    console = Console()
    cfg = AgentctlConfig.load()

    table = Table(title="Available Models")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Default", style="yellow")

    providers_to_check = [provider] if provider else list(cfg.providers.keys())

    for pname in providers_to_check:
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
            model_list = instance.list_models()

            default_model = pcfg.default_model if pcfg else None

            for m in model_list:
                is_default = "✓" if m == default_model else ""
                table.add_row(pname, m, is_default)
        except Exception as e:
            table.add_row(pname, f"[red]Error: {e}[/red]", "")

    console.print(table)
