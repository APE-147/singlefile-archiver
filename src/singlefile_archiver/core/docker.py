"""Docker service management functionality."""

import subprocess
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..services.docker_service import DockerService
from ..utils.config import get_config
from ..utils.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command("status")
def docker_status() -> None:
    """Show Docker service status."""
    docker_service = DockerService()
    
    table = Table(title="Docker Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    # Check Docker daemon
    is_running = docker_service.is_running()
    table.add_row(
        "Docker Daemon", 
        "✅ Running" if is_running else "❌ Stopped",
        "Ready for archiving" if is_running else "Start Docker to use archiving"
    )
    
    # Check SingleFile container
    if is_running:
        container_status = docker_service.get_container_status()
        if container_status:
            table.add_row("SingleFile Container", "✅ Available", f"Image: {container_status['image']}")
        else:
            table.add_row("SingleFile Container", "❌ Not available", "Will pull when needed")
    
    console.print(table)


@app.command("pull")
def pull_singlefile_image() -> None:
    """Pull the SingleFile Docker image."""
    docker_service = DockerService()
    
    if not docker_service.is_running():
        console.print("❌ Docker is not running. Please start Docker first.")
        raise typer.Exit(1)
    
    console.print("📥 Pulling SingleFile Docker image...")
    
    try:
        result = docker_service.pull_image()
        if result.success:
            console.print("✅ Successfully pulled SingleFile image")
        else:
            console.print(f"❌ Failed to pull image: {result.error}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error pulling image: {e}")
        logger.error(f"Error pulling Docker image: {e}")
        raise typer.Exit(1)


@app.command("start")
def start_docker() -> None:
    """Start Docker Desktop (macOS only)."""
    if not typer.get_os() == "darwin":
        console.print("❌ Docker start command is only supported on macOS")
        console.print("Please start Docker manually on your system")
        raise typer.Exit(1)
    
    console.print("🐳 Starting Docker Desktop...")
    
    try:
        subprocess.run(["open", "-a", "Docker"], check=True)
        console.print("✅ Docker Desktop startup initiated")
        console.print("ℹ️  Please wait for Docker to fully start before archiving")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to start Docker Desktop: {e}")
        console.print("Please start Docker Desktop manually")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("❌ Docker Desktop not found")
        console.print("Please install Docker Desktop from https://docker.com/products/docker-desktop")
        raise typer.Exit(1)


@app.command("stop")
def stop_docker() -> None:
    """Stop Docker Desktop (macOS only)."""
    if not typer.get_os() == "darwin":
        console.print("❌ Docker stop command is only supported on macOS")
        console.print("Please stop Docker manually on your system")
        raise typer.Exit(1)
    
    console.print("🛑 Stopping Docker Desktop...")
    
    try:
        # Kill Docker Desktop application
        subprocess.run(["pkill", "-f", "Docker Desktop"], check=False)
        console.print("✅ Docker Desktop stopped")
    except Exception as e:
        console.print(f"❌ Error stopping Docker: {e}")
        logger.error(f"Error stopping Docker: {e}")
        raise typer.Exit(1)


@app.command("restart")
def restart_docker() -> None:
    """Restart Docker Desktop (macOS only)."""
    if not typer.get_os() == "darwin":
        console.print("❌ Docker restart command is only supported on macOS")
        raise typer.Exit(1)
    
    console.print("🔄 Restarting Docker Desktop...")
    
    try:
        # Stop Docker
        subprocess.run(["pkill", "-f", "Docker Desktop"], check=False)
        console.print("🛑 Stopped Docker Desktop")
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Start Docker
        subprocess.run(["open", "-a", "Docker"], check=True)
        console.print("✅ Docker Desktop restart initiated")
        console.print("ℹ️  Please wait for Docker to fully start before archiving")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to restart Docker Desktop: {e}")
        raise typer.Exit(1)


@app.command("test")
def test_docker() -> None:
    """Test Docker setup with a simple container run."""
    docker_service = DockerService()
    
    if not docker_service.is_running():
        console.print("❌ Docker is not running. Please start Docker first.")
        raise typer.Exit(1)
    
    console.print("🧪 Testing Docker setup...")
    
    try:
        result = docker_service.test_connection()
        if result.success:
            console.print("✅ Docker test successful")
            console.print(f"ℹ️  {result.message}")
        else:
            console.print(f"❌ Docker test failed: {result.error}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error testing Docker: {e}")
        logger.error(f"Docker test error: {e}")
        raise typer.Exit(1)