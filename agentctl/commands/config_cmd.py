"""Config management commands."""

import click
from rich.console import Console
from rich.table import Table

from agentctl.config import AgentctlConfig, ProviderConfig


@click.group()
def config():
    """Manage provider configurations."""
    pass


@config.command("set")
@click.argument("provider")
@click.option("--api-key", help="API key for the provider")
@click.option("--endpoint", help="Custom endpoint URL")
@click.option("--model", "default_model", help="Default model for this provider")
def config_set(provider: str, api_key: str | None, endpoint: str | None, default_model: str | None):
    """Configure a provider."""
    cfg = AgentctlConfig.load()

    if provider not in cfg.providers:
        cfg.providers[provider] = ProviderConfig()

    p = cfg.providers[provider]
    if api_key:
        p.api_key = api_key
    if endpoint:
        p.endpoint = endpoint
    if default_model:
        p.default_model = default_model

    cfg.save()
    click.echo(f"✓ Provider '{provider}' configured.")


@config.command("show")
def config_show():
    """Show current configuration."""
    console = Console()
    cfg = AgentctlConfig.load()

    table = Table(title="Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("API Key", style="dim")
    table.add_column("Endpoint")
    table.add_column("Default Model", style="green")

    for name, p in cfg.providers.items():
        key_display = f"{p.api_key[:8]}..." if p.api_key else "—"
        table.add_row(name, key_display, p.endpoint or "default", p.default_model or "—")

    console.print(table)

    console.print(f"\n[bold]Defaults:[/bold]")
    console.print(f"  Provider: {cfg.defaults.provider}")
    console.print(f"  Temperature: {cfg.defaults.temperature}")
    console.print(f"  Max tokens: {cfg.defaults.max_tokens}")
    console.print(f"  Cost tracking: {'on' if cfg.costs.track else 'off'}")
    console.print(f"  Alert threshold: ${cfg.costs.alert_threshold:.2f}/mo")


@config.command("default")
@click.argument("provider")
def config_default(provider: str):
    """Set the default provider."""
    cfg = AgentctlConfig.load()
    cfg.defaults.provider = provider
    cfg.save()
    click.echo(f"✓ Default provider set to '{provider}'.")
