"""Failed URL retry functionality."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..services.csv_processor import CSVProcessor
from ..services.docker_service import DockerService
from ..utils.config import get_config
from ..utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command("failed")
def retry_failed_urls(
    failed_file: Optional[Path] = typer.Option(None, "--file", "-f", help="Failed URLs CSV file"),
    max_attempts: int = typer.Option(3, "--max-attempts", "-m", help="Maximum retry attempts"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
) -> None:
    """Retry failed URLs from previous archiving runs."""
    config = get_config()
    
    failed_path = failed_file or Path(config.project_dir) / "failed_urls.csv"
    
    if not failed_path.exists():
        console.print(f"❌ Failed URLs file not found: {failed_path}")
        console.print("No failed URLs to retry")
        return
    
    csv_processor = CSVProcessor()
    docker_service = DockerService()
    
    # Load failed URLs
    urls = csv_processor.load_urls(failed_path)
    if not urls:
        console.print("ℹ️  No URLs found in failed file")
        return
    
    console.print(f"🔄 Found {len(urls)} failed URLs to retry")
    
    if dry_run:
        console.print("🔍 Dry run mode - URLs that would be retried:")
        for i, url in enumerate(urls[:5]):  # Show first 5
            console.print(f"  {i+1}. {url}")
        if len(urls) > 5:
            console.print(f"  ... and {len(urls) - 5} more")
        return
    
    # Validate Docker is running
    if not docker_service.is_running():
        console.print("❌ Docker is not running. Please start Docker first.")
        raise typer.Exit(1)
    
    # Retry URLs
    successful_urls = []
    still_failed_urls = []
    output_path = output_dir or Path(config.archive_output_dir)
    
    for i, url in enumerate(urls, 1):
        console.print(f"🔄 Retrying {i}/{len(urls)}: {url}")
        
        success = False
        for attempt in range(max_attempts):
            try:
                result = docker_service.archive_url(url, output_path)
                if result.success:
                    successful_urls.append(url)
                    console.print(f"✅ Success on attempt {attempt + 1}")
                    success = True
                    break
                else:
                    console.print(f"❌ Attempt {attempt + 1} failed: {result.error}")
            except Exception as e:
                console.print(f"❌ Attempt {attempt + 1} error: {e}")
                logger.error(f"Retry error for {url}: {e}")
        
        if not success:
            still_failed_urls.append(url)
            console.print(f"❌ All {max_attempts} attempts failed for: {url}")
    
    # Update failed URLs file
    if still_failed_urls:
        csv_processor.save_urls(still_failed_urls, failed_path)
        console.print(f"⚠️  {len(still_failed_urls)} URLs still failing. Updated {failed_path}")
    else:
        # Remove the failed file if all succeeded
        failed_path.unlink()
        console.print("✅ All failed URLs successfully retried! Removed failed file.")
    
    console.print(f"📊 Retry complete: {len(successful_urls)} successful, {len(still_failed_urls)} still failed")


@app.command("status")
def retry_status() -> None:
    """Show retry status and failed URLs count."""
    config = get_config()
    failed_file = Path(config.project_dir) / "failed_urls.csv"
    
    from rich.table import Table
    
    table = Table(title="Retry Status")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")
    
    if failed_file.exists():
        csv_processor = CSVProcessor()
        urls = csv_processor.load_urls(failed_file)
        table.add_row("Failed URLs File", str(failed_file))
        table.add_row("Failed URLs Count", str(len(urls)))
        table.add_row("Status", "⚠️  URLs pending retry")
    else:
        table.add_row("Failed URLs File", "Not found")
        table.add_row("Failed URLs Count", "0")
        table.add_row("Status", "✅ No failed URLs")
    
    console.print(table)


@app.command("clear")
def clear_failed_urls(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Clear the failed URLs file."""
    config = get_config()
    failed_file = Path(config.project_dir) / "failed_urls.csv"
    
    if not failed_file.exists():
        console.print("ℹ️  No failed URLs file to clear")
        return
    
    if not confirm:
        response = typer.confirm("Are you sure you want to clear all failed URLs?")
        if not response:
            console.print("❌ Cancelled")
            return
    
    try:
        failed_file.unlink()
        console.print("✅ Failed URLs file cleared")
    except Exception as e:
        console.print(f"❌ Error clearing failed URLs file: {e}")
        raise typer.Exit(1)