#!/usr/bin/env python3
"""Main CLI entry point for SingleFile Archiver."""

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .core import archive, docker, monitor, retry, test
from .services.writer import StateWriter
from .utils.paths import get_project_dir

app = typer.Typer(
    name="singlefile-archiver",
    help="A comprehensive SingleFile URL archiving system with batch processing, file monitoring, and retry mechanisms",
    add_completion=False,
)
console = Console()

# Add subcommands
app.add_typer(archive.app, name="archive", help="Archive URLs from CSV files")
app.add_typer(monitor.app, name="monitor", help="Monitor folders for HTML files")
app.add_typer(retry.app, name="retry", help="Retry failed URLs")
app.add_typer(docker.app, name="docker", help="Manage Docker services")
app.add_typer(test.app, name="test", help="Run test scenarios")


@app.command()
def info() -> None:
    """Display application info and project directory."""
    project_dir = get_project_dir()

    table = Table(title="SingleFile Archiver Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Project Directory", str(project_dir))
    table.add_row("Config File", str(project_dir / "config.json"))
    table.add_row("State File", str(project_dir / "state.json"))

    console.print(table)


@app.command()
def write(
    key: str = typer.Option(..., "--key", "-k", help="Configuration key to write"),
    value: str = typer.Option(..., "--value", "-v", help="Configuration value to write"),
) -> None:
    """Write a key-value pair to the state file."""
    try:
        writer = StateWriter()
        writer.write(key, value)
        console.print(f"✓ Successfully wrote {key} = {value}")
    except Exception as e:
        console.print(f"❌ Error writing to state: {e}")
        raise typer.Exit(1)


@app.command()
def autostart(
    load: bool = typer.Option(False, "--load", help="Load the launch agent"),
    unload: bool = typer.Option(False, "--unload", help="Unload the launch agent"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show commands without executing"),
) -> None:
    """Manage macOS autostart via launchd (macOS only)."""
    if not typer.get_os() == "darwin":
        console.print("❌ Autostart is only supported on macOS")
        raise typer.Exit(1)

    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    plist_file = launch_agents_dir / "com.singlefile-archiver.plist"

    if load and unload:
        console.print("❌ Cannot specify both --load and --unload")
        raise typer.Exit(1)

    if not load and not unload:
        # Default to showing status
        if plist_file.exists():
            console.print(f"✓ Launch agent exists: {plist_file}")
            if dry_run:
                console.print("Commands that would be run:")
                console.print("  launchctl list | grep com.singlefile-archiver")
        else:
            console.print("❌ Launch agent not installed")
        return

    if load:
        if not plist_file.exists():
            console.print(f"❌ Launch agent file not found: {plist_file}")
            console.print("Run the installation script first to create the launch agent")
            raise typer.Exit(1)

        cmd = ["launchctl", "load", str(plist_file)]
        if dry_run:
            console.print(f"Would run: {' '.join(cmd)}")
        else:
            try:
                subprocess.run(cmd, check=True)
                console.print("✓ Launch agent loaded successfully")
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Failed to load launch agent: {e}")
                raise typer.Exit(1)

    if unload:
        cmd = ["launchctl", "unload", str(plist_file)]
        if dry_run:
            console.print(f"Would run: {' '.join(cmd)}")
        else:
            try:
                subprocess.run(cmd, check=True)
                console.print("✓ Launch agent unloaded successfully")
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Failed to unload launch agent: {e}")
                raise typer.Exit(1)


if __name__ == "__main__":
    app()
