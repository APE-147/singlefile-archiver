"""URL archiving functionality."""

import csv
import json
import re
import subprocess
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.progress import Progress, TaskID

from ..services.cookie_fetcher import CookieProvider
from ..services.csv_processor import CSVProcessor
from ..services.docker_service import DockerService
from ..utils.config import get_config
from ..utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


def check_duplicate_url(url: str, archive_dir: Path) -> bool:
    """Check if a URL has already been archived by searching for it in existing files"""
    if not archive_dir.exists():
        return False
    
    try:
        # Search for the URL in all HTML files
        for html_file in archive_dir.glob("*.html"):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    # Read first 10KB to look for the URL in meta tags or comments
                    content = f.read(10240)
                    if url in content:
                        logger.info(f"📋 URL already archived in: {html_file.name}")
                        return True
            except Exception:
                # Skip files that can't be read
                continue
                
        return False
        
    except Exception as e:
        logger.warning(f"Error checking for duplicates: {e}")
        return False


def get_page_title_filename(url: str, container_name: str) -> str:
    """Get page title and create filename, fallback to URL-based name if needed"""
    try:
        # Use SingleFile to get page info without saving
        cmd = [
            "docker", "exec", container_name,
            "npx", "single-file", url,
            "--output-json", "true",
            "--browser-headless", "true",
            "--browser-load-max-time", "15000"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0:
            try:
                page_info = json.loads(result.stdout)
                title = page_info.get('title', '').strip()
                
                if title:
                    # Clean title for filename
                    clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                    clean_title = clean_title[:50]  # Limit length
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    return f"{clean_title}_{timestamp}.html"
                    
            except json.JSONDecodeError:
                pass
                
    except Exception as e:
        logger.warning(f"Error getting page title for {url}: {e}")
    
    # Fallback to URL-based filename
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{domain}_{timestamp}.html"


def archive_single_url(url: str, container_name: str, output_dir: str) -> bool:
    """Archive a single URL using SingleFile Docker container"""
    try:
        filename = get_page_title_filename(url, container_name)
        
        cmd = [
            "docker", "exec", container_name,
            "npx", "single-file", url,
            "--filename-template", filename,
            "--output-directory", output_dir,
            "--browser-headless", "true",
            "--browser-load-max-time", "30000",
            "--browser-wait-until", "networkidle0"
        ]
        
        logger.info(f"🔄 Archiving: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully archived: {filename}")
            return True
        else:
            logger.error(f"❌ Failed to archive {url}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Timeout archiving {url}")
        return False
    except Exception as e:
        logger.error(f"❌ Error archiving {url}: {e}")
        return False


def process_urls_batch(urls: List[str], config) -> Tuple[List[str], List[str]]:
    """Process a batch of URLs, return (successful, failed)"""
    successful = []
    failed = []
    archive_dir = Path(config.archive_output_dir)
    
    for url in urls:
        # Check for duplicates
        if check_duplicate_url(url, archive_dir):
            logger.info(f"⏭️ Skipping URL - already archived: {url}")
            successful.append(url)
            continue
        
        # Try to archive with retries
        success = False
        for attempt in range(config.max_retries):
            if archive_single_url(url, config.docker_container, config.docker_output_dir):
                successful.append(url)
                success = True
                break
            else:
                if attempt < config.max_retries - 1:
                    logger.info(f"🔄 Retrying {url} (attempt {attempt + 2}/{config.max_retries})")
                    time.sleep(config.retry_delay)
        
        if not success:
            failed.append(url)
    
    return successful, failed


def export_failed_urls(failed_urls: List[str], output_file: Path) -> None:
    """Export failed URLs to a text file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Failed URLs Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total failed URLs: {len(failed_urls)}\n")
            f.write(f"# Format: One URL per line\n")
            f.write(f"# You can retry these URLs by running the retry command\n\n")
            
            for url in failed_urls:
                f.write(f"{url}\n")
        
        logger.info(f"📄 Exported {len(failed_urls)} failed URLs to: {output_file}")
    except Exception as e:
        logger.error(f"❌ Error exporting failed URLs: {e}")


@app.command("urls")
def archive_urls(
    csv_file: Path = typer.Argument(..., help="CSV file containing URLs to archive"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Batch size for processing"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    cookies_file: Optional[Path] = typer.Option(None, "--cookies-file", "-c", help="Cookies file to inject into the browser"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
) -> None:
    """Archive URLs from a CSV file using SingleFile Docker container."""
    if not csv_file.exists():
        console.print(f"❌ CSV file not found: {csv_file}")
        raise typer.Exit(1)
    
    config = get_config()
    processor = CSVProcessor()
    
    # Load URLs from CSV
    urls = processor.load_urls(csv_file)
    if not urls:
        console.print("❌ No valid URLs found in CSV file")
        raise typer.Exit(1)
    
    console.print(f"📊 Found {len(urls)} URLs to process")
    
    if dry_run:
        console.print("🔍 Dry run mode - showing what would be done:")
        for i, url in enumerate(urls[:10], 1):
            console.print(f"  {i}. {url}")
        if len(urls) > 10:
            console.print(f"  ... and {len(urls) - 10} more URLs")
        return
    
    # Process URLs in batches
    all_successful = []
    all_failed = []
    
    with Progress() as progress:
        task = progress.add_task("Archiving URLs", total=len(urls))
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            console.print(f"\n📦 Processing batch {i//batch_size + 1} ({len(batch)} URLs)...")
            
            successful, failed = process_urls_batch(batch, config)
            all_successful.extend(successful)
            all_failed.extend(failed)
            
            progress.update(task, advance=len(batch))
    
    # Export failed URLs if any
    if all_failed:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        failed_file = Path(f"failed_urls_{timestamp}.txt")
        export_failed_urls(all_failed, failed_file)
    
    # Summary
    console.print(f"\n📈 Summary:")
    console.print(f"  ✅ Successful: {len(all_successful)}")
    console.print(f"  ❌ Failed: {len(all_failed)}")
    console.print(f"  📊 Success rate: {len(all_successful)/(len(all_successful)+len(all_failed))*100:.1f}%")
    
    config = get_config()
    docker_service = DockerService()
    csv_processor = CSVProcessor()
    
    # Validate Docker is running
    if not docker_service.is_running():
        console.print("❌ Docker is not running. Please start Docker first.")
        raise typer.Exit(1)
    
    # Load URLs from CSV
    urls = csv_processor.load_urls(csv_file)
    if not urls:
        console.print("❌ No valid URLs found in CSV file")
        raise typer.Exit(1)
    
    console.print(f"📋 Found {len(urls)} URLs to archive")
    
    if dry_run:
        console.print("🔍 Dry run mode - showing what would be done:")
        for i, url in enumerate(urls[:5]):  # Show first 5
            console.print(f"  {i+1}. {url}")
        if len(urls) > 5:
            console.print(f"  ... and {len(urls) - 5} more")
        return
    
    # Process URLs in batches
    failed_urls = []
    output_path = output_dir or Path(config.archive_output_dir)
    
    with Progress() as progress:
        task = progress.add_task("Archiving URLs...", total=len(urls))
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            console.print(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} URLs)")
            
            for url in batch:
                try:
                    result = docker_service.archive_url(url, output_path, cookies_file=cookies_file)
                    if not result.success:
                        failed_urls.append(url)
                        console.print(f"❌ Failed to archive: {url}")
                    else:
                        console.print(f"✅ Archived: {url}")
                except Exception as e:
                    logger.error(f"Error archiving {url}: {e}")
                    failed_urls.append(url)
                    console.print(f"❌ Error archiving: {url}")
                
                progress.advance(task)
    
    # Save failed URLs for retry
    if failed_urls:
        failed_file = Path(config.project_dir) / "failed_urls.csv"
        csv_processor.save_urls(failed_urls, failed_file)
        console.print(f"⚠️  {len(failed_urls)} URLs failed. Saved to {failed_file}")
    
    console.print(f"✅ Archive complete! {len(urls) - len(failed_urls)}/{len(urls)} successful")


@app.command("single")
def archive_single_url(
    url: str = typer.Argument(..., help="Single URL to archive"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    cookies_file: Optional[Path] = typer.Option(None, "--cookies-file", "-c", help="Cookies file to inject into the browser"),
) -> None:
    """Archive a single URL."""
    config = get_config()
    docker_service = DockerService()
    
    if not docker_service.is_running():
        console.print("❌ Docker is not running. Please start Docker first.")
        raise typer.Exit(1)
    
    output_path = output_dir or Path(config.archive_output_dir)
    console.print(f"🔄 Archiving: {url}")
    
    try:
        result = docker_service.archive_url(url, output_path, cookies_file=cookies_file)
        if result.success:
            console.print(f"✅ Successfully archived to: {result.output_file}")
        else:
            console.print(f"❌ Failed to archive: {result.error}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error: {e}")
        raise typer.Exit(1)


@app.command("auto-cookie")
def archive_with_cookie_update(
    urls: List[str] = typer.Argument(..., help="One or more URLs to archive"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
) -> None:
    """Archive URLs using cookie-update data when available."""

    if not urls:
        console.print("❌ Please provide at least one URL to archive")
        raise typer.Exit(1)

    config = get_config()
    docker_service = DockerService()
    provider = CookieProvider()

    if not docker_service.is_running():
        console.print("❌ Docker is not running. Please start Docker first.")
        raise typer.Exit(1)

    output_path = output_dir or Path(config.archive_output_dir)
    cookie_files: Dict[str, Path] = {}
    cookie_status: Dict[str, bool] = {}
    temp_files: List[Path] = []

    def _safe_token(value: str) -> str:
        sanitized = [ch if ch.isalnum() else "_" for ch in value]
        token = "".join(sanitized).strip("_")
        return token or "domain"

    def _write_cookie_file(domain: str, cookies: List[Dict[str, object]]) -> Path:
        safe = _safe_token(domain)
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".cookies.json",
            prefix=f"singlefile_{safe}_",
            delete=False,
            encoding="utf-8",
        ) as handle:
            json.dump(cookies, handle, ensure_ascii=False, indent=2)
            temp_path = Path(handle.name)
        temp_files.append(temp_path)
        return temp_path

    try:
        if dry_run:
            console.print("🔍 Dry run - cookie-update lookup:")
            for url in urls:
                domain = CookieProvider.normalize_domain(url) or url
                bundle = provider.get_bundle(url)
                if bundle and bundle.singlefile:
                    console.print(
                        f"  {url} -> {domain}: {len(bundle.singlefile)} cookies available"
                    )
                else:
                    console.print(f"  {url} -> {domain}: no cookies from cookie-update")
            return

        successes = 0
        failures: List[Tuple[str, str]] = []

        for url in urls:
            domain = CookieProvider.normalize_domain(url) or url
            singlefile_cookies = provider.get_singlefile_cookies(url)
            cookies_path: Optional[Path] = None

            if singlefile_cookies:
                cookies_path = cookie_files.get(domain)
                if not cookies_path:
                    cookies_path = _write_cookie_file(domain, singlefile_cookies)
                    cookie_files[domain] = cookies_path
                    console.print(
                        f"🔐 cookie-update: using {len(singlefile_cookies)} cookies for {domain}"
                    )
                elif domain not in cookie_status:
                    console.print(f"🔐 cookie-update: reusing cached cookies for {domain}")
                cookie_status[domain] = True
            else:
                if domain not in cookie_status:
                    console.print(f"ℹ️ cookie-update: no cookies available for {domain}")
                    cookie_status[domain] = False

            console.print(f"🔄 Archiving: {url}")
            try:
                result = docker_service.archive_url(url, output_path, cookies_file=cookies_path)
            except Exception as exc:
                logger.error("Error archiving %s: %s", url, exc)
                failures.append((url, str(exc)))
                console.print(f"  ❌ Error: {exc}")
                continue

            if result.success:
                successes += 1
                destination = result.output_file or output_path
                console.print(f"  ✅ Archived to: {destination}")
            else:
                reason = result.error or "unknown error"
                failures.append((url, reason))
                console.print(f"  ❌ Failed: {reason}")

        console.print("\n📈 Summary:")
        console.print(f"  ✅ Successful: {successes}")
        console.print(f"  ❌ Failed: {len(failures)}")
        if failures:
            console.print("  ⚠️  Failed URLs:")
            for failed_url, reason in failures:
                console.print(f"    - {failed_url}: {reason}")
            raise typer.Exit(1)

    finally:
        for path in temp_files:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                logger.debug("Failed to remove temp cookie file: %s", path)
