"""Run command — one-shot agent completion."""

import asyncio

import click
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from agentctl.config import AgentctlConfig
from agentctl.providers import Message, get_provider

import agentctl.providers.ollama  # noqa: F401
import agentctl.providers.anthropic_provider  # noqa: F401
import agentctl.providers.openai_provider  # noqa: F401


@click.command()
@click.argument("model", required=False)
@click.argument("prompt", required=True)
@click.option("--provider", "-p", help="Provider to use")
@click.option("--temperature", "-t", type=float, help="Temperature")
@click.option("--max-tokens", type=int, help="Max output tokens")
@click.option("--system", "-s", help="System prompt")
@click.option("--stream/--no-stream", default=True, help="Stream output")
def run(
    model: str | None,
    prompt: str,
    provider: str | None,
    temperature: float | None,
    max_tokens: int | None,
    system: str | None,
    stream: bool,
):
    """Run a one-shot completion.

    Examples:

        agentctl run "Explain transformers"

        agentctl run gpt-4o "Explain transformers"

        agentctl run --provider ollama llama3.1:8b "Hello"
    """
    asyncio.run(_run(model, prompt, provider, temperature, max_tokens, system, stream))


async def _run(
    model: str | None,
    prompt: str,
    provider_name: str | None,
    temperature: float | None,
    max_tokens: int | None,
    system: str | None,
    stream: bool,
):
    console = Console()
    cfg = AgentctlConfig.load()

    pname, pcfg = cfg.get_provider(provider_name)
    model = model or pcfg.default_model

    provider_cls = get_provider(pname)

    init_kwargs = {}
    if pcfg.api_key:
        init_kwargs["api_key"] = pcfg.api_key
    if pcfg.endpoint:
        init_kwargs["endpoint"] = pcfg.endpoint

    instance = provider_cls(**init_kwargs)

    messages = []
    if system:
        messages.append(Message(role="system", content=system))
    messages.append(Message(role="user", content=prompt))

    kwargs = {}
    if model:
        kwargs["model"] = model
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if stream:
        collected = ""
        with Live(console=console, refresh_per_second=10) as live:
            async for chunk in instance.stream(messages, **kwargs):
                collected += chunk
                live.update(Markdown(collected))
        console.print()
    else:
        with console.status("[bold cyan]Thinking...[/bold cyan]"):
            response = await instance.complete(messages, **kwargs)

        console.print(Markdown(response.content))
        console.print()
        console.print(
            Panel(
                f"[dim]Model: {response.model} | "
                f"Tokens: {response.input_tokens}→{response.output_tokens} | "
                f"Cost: ${response.cost:.4f} | "
                f"Latency: {response.latency_ms:.0f}ms[/dim]",
                style="dim",
            )
        )
