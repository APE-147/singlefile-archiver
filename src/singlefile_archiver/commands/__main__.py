"""Command-line interface for optimize command."""

import typer
from singlefile_archiver.commands.optimize import optimize_filenames_command

if __name__ == "__main__":
    # Allow running as: python -m singlefile_archiver.commands.optimize
    typer.run(optimize_filenames_command)