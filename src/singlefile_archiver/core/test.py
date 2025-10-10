"""Test scenarios for the archiver system."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..services.csv_processor import CSVProcessor
from ..services.docker_service import DockerService
from ..utils.config import get_config
from ..utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command("all")
def run_all_tests() -> None:
    """Run all available test scenarios."""
    console.print("🧪 Running all test scenarios...")

    tests = [
        ("Docker Connection", test_docker_connection),
        ("Configuration", test_configuration),
        ("Directory Structure", test_directories),
        ("CSV Processing", test_csv_processing),
    ]

    results = []

    for test_name, test_func in tests:
        console.print(f"\n▶️  Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, "✅ Pass" if success else "❌ Fail"))
        except Exception as e:
            results.append((test_name, f"❌ Error: {str(e)[:50]}"))
            logger.error(f"Test {test_name} error: {e}")

    # Display results
    table = Table(title="Test Results Summary")
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="green")

    for test_name, result in results:
        table.add_row(test_name, result)

    console.print(table)


@app.command("docker")
def test_docker_connection() -> bool:
    """Test Docker connection and SingleFile image."""
    console.print("🐳 Testing Docker connection...")

    docker_service = DockerService()

    # Test Docker daemon
    if not docker_service.is_running():
        console.print("❌ Docker daemon is not running")
        return False

    console.print("✅ Docker daemon is running")

    # Test Docker connection
    try:
        result = docker_service.test_connection()
        if result.success:
            console.print("✅ Docker connection test passed")
            return True
        else:
            console.print(f"❌ Docker connection test failed: {result.error}")
            return False
    except Exception as e:
        console.print(f"❌ Docker test error: {e}")
        return False


@app.command("config")
def test_configuration() -> bool:
    """Test configuration loading and validation."""
    console.print("⚙️  Testing configuration...")

    try:
        config = get_config()

        # Check required directories
        required_dirs = [
            "project_dir",
            "archive_output_dir",
            "monitor_watch_dir",
            "monitor_archive_dir"
        ]

        for dir_attr in required_dirs:
            if hasattr(config, dir_attr):
                dir_path = getattr(config, dir_attr)
                console.print(f"✅ {dir_attr}: {dir_path}")
            else:
                console.print(f"❌ Missing config: {dir_attr}")
                return False

        console.print("✅ Configuration test passed")
        return True

    except Exception as e:
        console.print(f"❌ Configuration test failed: {e}")
        return False


@app.command("dirs")
def test_directories() -> bool:
    """Test directory structure and permissions."""
    console.print("📁 Testing directory structure...")

    try:
        config = get_config()

        # Test project directory
        project_dir = Path(config.project_dir)
        if not project_dir.exists():
            console.print(f"📁 Creating project directory: {project_dir}")
            project_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"✅ Project directory: {project_dir}")

        # Test write permissions
        test_file = project_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            console.print("✅ Write permissions OK")
        except Exception as e:
            console.print(f"❌ Write permission test failed: {e}")
            return False

        # Test archive output directory
        archive_dir = Path(config.archive_output_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Archive directory: {archive_dir}")

        console.print("✅ Directory structure test passed")
        return True

    except Exception as e:
        console.print(f"❌ Directory test failed: {e}")
        return False


@app.command("csv")
def test_csv_processing() -> bool:
    """Test CSV file processing functionality."""
    console.print("📄 Testing CSV processing...")

    try:
        csv_processor = CSVProcessor()
        config = get_config()

        # Create test CSV
        test_urls = [
            "https://example.com",
            "https://github.com",
            "https://google.com"
        ]

        test_csv = Path(config.project_dir) / "test_urls.csv"

        # Test saving URLs
        csv_processor.save_urls(test_urls, test_csv)
        console.print(f"✅ Created test CSV: {test_csv}")

        # Test loading URLs
        loaded_urls = csv_processor.load_urls(test_csv)

        if loaded_urls == test_urls:
            console.print("✅ CSV round-trip test passed")
        else:
            console.print("❌ CSV round-trip test failed")
            console.print(f"Expected: {test_urls}")
            console.print(f"Got: {loaded_urls}")
            return False

        # Clean up
        test_csv.unlink()
        console.print("✅ CSV processing test passed")
        return True

    except Exception as e:
        console.print(f"❌ CSV processing test failed: {e}")
        return False


@app.command("archive")
def test_archive_workflow(
    test_url: str = typer.Option("https://example.com", "--url", help="URL to test archiving"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="Run in dry-run mode"),
) -> None:
    """Test the complete archive workflow."""
    console.print("🏛️  Testing archive workflow...")

    docker_service = DockerService()
    config = get_config()

    # Check prerequisites
    if not docker_service.is_running():
        console.print("❌ Docker is not running. Cannot test archive workflow.")
        raise typer.Exit(1)

    console.print(f"🔗 Test URL: {test_url}")
    console.print(f"🔍 Dry run: {dry_run}")

    if dry_run:
        console.print("✅ Archive workflow test (dry run) - would archive URL")
        console.print(f"   Output would go to: {config.archive_output_dir}")
        return

    # Actual archive test
    try:
        output_path = Path(config.archive_output_dir)
        result = docker_service.archive_url(test_url, output_path)

        if result.success:
            console.print(f"✅ Archive test successful: {result.output_file}")
        else:
            console.print(f"❌ Archive test failed: {result.error}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ Archive test error: {e}")
        logger.error(f"Archive test error: {e}")
        raise typer.Exit(1)
