"""Main CLI entrypoint for agentctl."""

import click
from rich.console import Console

from agentctl import __version__
from agentctl.commands.config_cmd import config
from agentctl.commands.models import models
from agentctl.commands.run import run
from agentctl.commands.session import session
from agentctl.commands.costs import costs
from agentctl.commands.compare import compare
from agentctl.commands.logs import logs

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="agentctl")
@click.pass_context
def main(ctx: click.Context) -> None:
    """agentctl — kubectl for AI agents.

    Manage, monitor, and debug AI agents across providers from one CLI.
    """
    ctx.ensure_object(dict)
    ctx.obj["console"] = console


main.add_command(config)
main.add_command(models)
main.add_command(run)
main.add_command(session)
main.add_command(costs)
main.add_command(compare)
main.add_command(logs)


if __name__ == "__main__":
    main()
