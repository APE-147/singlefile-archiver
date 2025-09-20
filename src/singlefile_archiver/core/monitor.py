"""File monitoring functionality."""

import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..services.file_monitor import FileMonitor
from ..utils.config import get_config
from ..utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command("start")
def start_monitoring(
    watch_dir: Optional[Path] = typer.Option(None, "--watch", "-w", help="Directory to monitor"),
    archive_dir: Optional[Path] = typer.Option(None, "--archive", "-a", help="Archive directory"),
    pattern: str = typer.Option("*.html", "--pattern", "-p", help="File pattern to match"),
    interval: int = typer.Option(5, "--interval", "-i", help="Check interval in seconds"),
) -> None:
    """Start monitoring a directory for HTML files."""
    config = get_config()
    
    watch_path = watch_dir or Path(config.monitor_watch_dir)
    archive_path = archive_dir or Path(config.monitor_archive_dir)
    
    if not watch_path.exists():
        console.print(f"❌ Watch directory does not exist: {watch_path}")
        raise typer.Exit(1)
    
    archive_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"👀 Starting file monitor...")
    console.print(f"   Watch directory: {watch_path}")
    console.print(f"   Archive directory: {archive_path}")
    console.print(f"   Pattern: {pattern}")
    console.print(f"   Check interval: {interval}s")
    console.print("Press Ctrl+C to stop")
    
    monitor = FileMonitor(
        watch_dir=watch_path,
        archive_dir=archive_path,
        check_interval=interval
    )
    
    try:
        monitor.start_monitoring(use_watchdog=True)
    except KeyboardInterrupt:
        console.print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        console.print(f"❌ Monitor error: {e}")
        logger.error(f"Monitor error: {e}")
        raise typer.Exit(1)


@app.command("once")
def monitor_once(
    watch_dir: Optional[Path] = typer.Option(None, "--watch", "-w", help="Directory to monitor"),
    archive_dir: Optional[Path] = typer.Option(None, "--archive", "-a", help="Archive directory"),
    pattern: str = typer.Option("*.html", "--pattern", "-p", help="File pattern to match"),
) -> None:
    """Run monitoring once and exit."""
    config = get_config()
    
    watch_path = watch_dir or Path(config.monitor_watch_dir)
    archive_path = archive_dir or Path(config.monitor_archive_dir)
    
    if not watch_path.exists():
        console.print(f"❌ Watch directory does not exist: {watch_path}")
        raise typer.Exit(1)
    
    archive_path.mkdir(parents=True, exist_ok=True)
    
    monitor = FileMonitor(
        watch_dir=watch_path,
        archive_dir=archive_path,
        check_interval=interval
    )
    
    try:
        moved_count = monitor.process_files()
        if moved_count > 0:
            console.print(f"✅ Moved {moved_count} files to archive")
        else:
            console.print("ℹ️  No matching files found")
    except Exception as e:
        console.print(f"❌ Monitor error: {e}")
        logger.error(f"Monitor error: {e}")
        raise typer.Exit(1)


@app.command("status")
def monitor_status() -> None:
    """Show monitoring configuration and status."""
    config = get_config()
    
    from rich.table import Table
    
    table = Table(title="File Monitor Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")
    
    watch_dir = Path(config.monitor_watch_dir)
    archive_dir = Path(config.monitor_archive_dir)
    
    table.add_row(
        "Watch Directory", 
        str(watch_dir), 
        "✅ Exists" if watch_dir.exists() else "❌ Missing"
    )
    table.add_row(
        "Archive Directory", 
        str(archive_dir), 
        "✅ Exists" if archive_dir.exists() else "📁 Will be created"
    )
    
    console.print(table)


@app.command("scan")
def scan_existing_files(
    directory: Optional[Path] = typer.Option(None, "--directory", "-d", help="Directory to scan"),
    move: bool = typer.Option(False, "--move", help="Actually move matching files"),
) -> None:
    """Scan incoming directory for files that match archiving criteria."""
    config = get_config()
    directory = directory or Path(config.monitor_watch_dir)
    archive_dir = Path(config.monitor_archive_dir)
    
    if not directory.exists():
        console.print(f"❌ Directory does not exist: {directory}")
        raise typer.Exit(1)
    
    file_monitor = FileMonitor(directory, archive_dir)
    
    console.print(f"🔍 Scanning {directory} for matching HTML files...")
    
    matching_files = []
    for file_path in directory.glob("*.html"):
        if file_monitor.should_move_file(file_path):
            matching_files.append(file_path)
    
    if not matching_files:
        console.print("📦 No matching files found")
        return
    
    console.print(f"Found {len(matching_files)} matching files:")
    
    from rich.table import Table
    table = Table()
    table.add_column("File", style="cyan")
    table.add_column("Pattern", style="green")
    table.add_column("Size", style="yellow")
    
    for file_path in sorted(matching_files):
        filename = file_path.name
        
        # Determine which pattern matched
        if "X 上的" in filename:
            pattern = "Contains 'X 上的'"
        else:
            pattern = "Timestamp pattern"
        
        size = f"{file_path.stat().st_size:,} bytes"
        table.add_row(filename[:80] + "..." if len(filename) > 80 else filename, pattern, size)
    
    console.print(table)
    
    if move:
        console.print(f"\n📦 Moving {len(matching_files)} files to archive...")
        moved_count = 0
        
        for file_path in matching_files:
            if file_monitor.move_file_to_archive(file_path):
                moved_count += 1
        
        console.print(f"✅ Successfully moved {moved_count} files to archive")
    else:
        console.print("\n💡 Use --move to actually move these files to archive")