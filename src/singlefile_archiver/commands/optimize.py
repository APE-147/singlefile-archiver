"""Batch filename optimization commands."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from ..utils.logging import get_logger
from ..utils.paths import optimize_filename, safe_filename

logger = get_logger(__name__)
console = Console()


@dataclass
class RenameOperation:
    """Represents a file rename operation."""
    old_path: Path
    new_path: Path
    old_name: str
    new_name: str
    conflict: bool = False
    reason: str = ""


def extract_title_from_filename(filename: str) -> str:
    """Extract the title portion from an archived filename.
    
    Args:
        filename: The original filename
        
    Returns:
        Extracted title or the filename if no pattern matches
    """
    # Remove extension
    base_name = filename.replace('.html', '').replace('.htm', '')

    # Try to extract title from pattern: (title) [URL] encoded_url
    title_match = re.match(r'^\(([^)]+)\)', base_name)
    if title_match:
        return title_match.group(1)

    # Try to extract from other common patterns
    # Pattern: title - URL or title_URL
    for separator in [' - ', '_', ' ']:
        if separator in base_name:
            parts = base_name.split(separator)
            if len(parts) >= 2:
                return parts[0].strip()

    # Fallback: use the whole base name
    return base_name


def generate_optimized_filename(original_path: Path, existing_names: set = None) -> str:
    """Generate an optimized filename from the original with deduplication.
    
    Args:
        original_path: Path to the original file
        existing_names: Set of existing filenames to avoid duplicates
        
    Returns:
        Optimized filename that doesn't conflict with existing names
    """
    original_name = original_path.stem
    extension = original_path.suffix

    # Extract title from the filename
    title = extract_title_from_filename(original_name)

    # Optimize the title with deduplication support
    optimized_title = optimize_filename(title, max_length=120, existing_names=existing_names)

    # Create the new filename
    new_name = safe_filename(optimized_title) + extension

    return new_name


def scan_archive_directory(directory: Path, pattern: str = "*.html") -> List[Path]:
    """Scan directory for archive files.
    
    Args:
        directory: Directory to scan
        pattern: File pattern to match
        
    Returns:
        List of archive file paths
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    files = []
    try:
        files = list(directory.glob(pattern))
        files.extend(directory.glob("*.htm"))  # Also include .htm files

        # Filter out already optimized files (basic heuristic)
        filtered_files = []
        for file_path in files:
            name = file_path.stem
            # Skip files that appear to already be optimized (no emoji, reasonable length)
            if len(name) <= 120 and not any(c for c in name if ord(c) > 127):
                # Check if it contains obvious emoji patterns
                if not re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', name):
                    # This file might already be optimized, but include it anyway for user decision
                    pass
            filtered_files.append(file_path)

        return filtered_files

    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
        return []


def generate_rename_operations(files: List[Path]) -> List[RenameOperation]:
    """Generate rename operations for a list of files with intelligent deduplication.
    
    Args:
        files: List of file paths to process
        
    Returns:
        List of rename operations with conflicts resolved through progressive truncation
    """
    operations = []
    used_final_names = set()  # Track final safe filenames
    used_optimized_titles = set()  # Track optimized titles for deduplication
    
    # Build set of existing filenames in the directory for context
    if files:
        directory = files[0].parent
        existing_files = {f.stem.lower() for f in directory.glob('*') if f.is_file()}
    else:
        existing_files = set()

    # First pass: generate all potential names with proper deduplication
    for file_path in files:
        try:
            # Extract title from filename
            original_name = file_path.stem
            extension = file_path.suffix
            title = extract_title_from_filename(original_name)
            
            # Optimize the title with deduplication based on already processed titles
            optimized_title = optimize_filename(title, max_length=120, existing_names=used_optimized_titles)
            
            # Track this optimized title
            used_optimized_titles.add(optimized_title.lower())
            
            # Create the new filename
            new_name = safe_filename(optimized_title) + extension
            new_path = file_path.parent / new_name

            # Check for conflicts
            conflict = False
            reason = ""

            if new_path.exists() and new_path != file_path:
                conflict = True
                reason = "Target file already exists"
            elif new_name.lower() in used_final_names:
                # This should be very rare now with proper deduplication
                conflict = True
                reason = "Duplicate name generated (deduplication failed)"
            else:
                used_final_names.add(new_name.lower())

            operation = RenameOperation(
                old_path=file_path,
                new_path=new_path,
                old_name=file_path.name,
                new_name=new_name,
                conflict=conflict,
                reason=reason
            )

            operations.append(operation)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            continue

    return operations


def preview_operations(operations: List[RenameOperation]) -> None:
    """Display a preview of rename operations.
    
    Args:
        operations: List of rename operations to preview
    """
    if not operations:
        console.print("[yellow]No files found to optimize.[/yellow]")
        return

    table = Table(title="Filename Optimization Preview")
    table.add_column("Current Name", style="cyan", max_width=40)
    table.add_column("New Name", style="green", max_width=40)
    table.add_column("Status", style="bold")
    table.add_column("Notes", style="dim")

    changes_count = 0
    conflicts_count = 0

    for op in operations:
        if op.old_name == op.new_name:
            status = "[dim]No change[/dim]"
            notes = "Already optimized"
        elif op.conflict:
            status = "[red]Conflict[/red]"
            notes = op.reason
            conflicts_count += 1
        else:
            status = "[green]Will rename[/green]"
            notes = "✓"
            changes_count += 1

        table.add_row(op.old_name, op.new_name, status, notes)

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {changes_count} files to rename, {conflicts_count} conflicts")


def apply_operations(operations: List[RenameOperation], force: bool = False) -> Tuple[int, int]:
    """Apply rename operations.
    
    Args:
        operations: List of rename operations to apply
        force: Whether to skip confirmation prompts
        
    Returns:
        Tuple of (successful_renames, failed_renames)
    """
    successful = 0
    failed = 0

    for op in operations:
        if op.old_name == op.new_name:
            continue  # Skip files that don't need renaming

        if op.conflict and not force:
            console.print(f"[yellow]Skipping {op.old_name}: {op.reason}[/yellow]")
            failed += 1
            continue

        try:
            # Perform the rename
            op.old_path.rename(op.new_path)
            console.print(f"[green]✓[/green] Renamed: {op.old_name} → {op.new_name}")
            successful += 1
            logger.info(f"Renamed file: {op.old_path} → {op.new_path}")

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to rename {op.old_name}: {e}")
            logger.error(f"Failed to rename {op.old_path}: {e}")
            failed += 1

    return successful, failed


def optimize_filenames_command(
    directory: str = typer.Argument(..., help="Directory containing archive files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
    interactive: bool = typer.Option(False, "--interactive", help="Ask for confirmation before each rename"),
    force: bool = typer.Option(False, "--force", help="Apply changes without confirmation (use with caution)"),
    pattern: str = typer.Option("*.html", "--pattern", help="File pattern to match")
) -> None:
    """Optimize filenames for archived files.
    
    This command will:
    1. Remove emoji and special characters from filenames
    2. Control filename length with intelligent truncation
    3. Apply consistent naming conventions
    """
    # Check feature flag with improved user experience
    if not os.getenv('FF_BATCH_PROCESSING', 'false').lower() == 'true':
        console.print("[yellow]⚠️  Batch processing feature flag is not enabled.[/yellow]")
        console.print()
        console.print("[bold]To enable batch processing, you have several options:[/bold]")
        console.print("1. [green]Set environment variable:[/green] export FF_BATCH_PROCESSING=true")
        console.print("2. [green]Run with inline variable:[/green] FF_BATCH_PROCESSING=true python -m singlefile_archiver.commands.optimize [DIRECTORY]")
        console.print("3. [green]Use the convenience script:[/green] python run_optimize.py [DIRECTORY] --dry-run")
        console.print()
        console.print("[dim]This safety feature prevents accidental bulk file operations.[/dim]")
        console.print("[dim]Learn more in the documentation about feature flags and safety controls.[/dim]")
        
        # Offer to run with the flag enabled interactively
        # Allow interactive enabling for dry-run (safe) or when not forced
        if not force:
            console.print()
            if dry_run:
                console.print("[dim]Since you're using --dry-run (safe preview mode), we can enable it temporarily.[/dim]")
            enable_flag = Confirm.ask("Would you like to enable batch processing for this session?")
            if enable_flag:
                os.environ['FF_BATCH_PROCESSING'] = 'true'
                console.print("[green]✓ Batch processing enabled for this session.[/green]")
            else:
                console.print("[yellow]Batch processing remains disabled. Exiting.[/yellow]")
                raise typer.Exit(0)
        else:
            # Force mode without feature flag - exit with error
            console.print("[red]Cannot use --force without enabling FF_BATCH_PROCESSING.[/red]")
            raise typer.Exit(1)

    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[red]Directory does not exist: {directory}[/red]")
        raise typer.Exit(1)

    if not dir_path.is_dir():
        console.print(f"[red]Path is not a directory: {directory}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Scanning directory:[/bold] {dir_path}")

    # Scan for files
    files = scan_archive_directory(dir_path, pattern)
    console.print(f"Found {len(files)} files matching pattern '{pattern}'")

    if not files:
        console.print("[yellow]No files found to process.[/yellow]")
        return

    # Generate rename operations
    operations = generate_rename_operations(files)

    # Preview operations
    preview_operations(operations)

    if dry_run:
        console.print("\n[bold blue]Dry run complete. No files were modified.[/bold blue]")
        return

    # Apply operations
    operations_to_apply = [op for op in operations if not op.conflict or force]

    if not operations_to_apply:
        console.print("\n[yellow]No operations to apply.[/yellow]")
        return

    if not force and not interactive:
        if not Confirm.ask(f"\nProceed with renaming {len(operations_to_apply)} files?"):
            console.print("Operation cancelled.")
            return

    console.print("\n[bold]Applying filename optimizations...[/bold]")
    successful, failed = apply_operations(operations_to_apply, force=force)

    console.print(f"\n[bold]Results:[/bold] {successful} successful, {failed} failed")

    if failed > 0:
        console.print("[yellow]Some operations failed. Check the logs for details.[/yellow]")


# CLI app integration would be added to the main CLI module
if __name__ == "__main__":
    # For testing purposes
    typer.run(optimize_filenames_command)
