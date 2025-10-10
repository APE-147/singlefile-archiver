"""Configuration management."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

from .paths import get_project_dir


def _get_default_data_dir() -> str:
    """Get default data directory from environment or fallback to user directory."""
    return os.getenv(
        "SINGLEFILE_DATA_DIR",
        str(Path.home() / ".local" / "share" / "singlefile")
    )


def _get_default_archive_dir() -> str:
    """Get default archive directory from environment or fallback to data subdirectory."""
    return os.getenv(
        "SINGLEFILE_ARCHIVE_DIR",
        str(Path(_get_default_data_dir()) / "archive")
    )


def _get_default_incoming_dir() -> str:
    """Get default incoming directory from environment or fallback to data subdirectory."""
    return os.getenv(
        "SINGLEFILE_INCOMING_DIR",
        str(Path(_get_default_data_dir()) / "incoming")
    )


class Config(BaseModel):
    """Application configuration model."""

    # Project paths
    project_dir: str = Field(default_factory=lambda: str(get_project_dir()))

    # Archive settings
    archive_output_dir: str = Field(default_factory=_get_default_archive_dir)
    archive_batch_size: int = Field(default=10)
    max_retries: int = Field(default=10)
    retry_delay: int = Field(default=2)

    # Monitor settings
    monitor_watch_dir: str = Field(default_factory=_get_default_incoming_dir)
    monitor_archive_dir: str = Field(default_factory=_get_default_archive_dir)
    monitor_pattern: str = Field(default="*.html")
    monitor_interval: int = Field(default=2)

    # Docker settings
    docker_image: str = Field(default="capsulecode/singlefile")
    docker_container: str = Field(default="singlefile-cli")
    docker_output_dir: str = Field(default="/data/archive")
    docker_timeout: int = Field(default=300)
    docker_cookies_file: Optional[str] = Field(default=None)
    docker_cookies_mount_path: str = Field(default="/tmp/singlefile-cookies.json")

    # Retry settings
    max_retry_attempts: int = Field(default=10)
    retry_delay: int = Field(default=2)

    # Logging
    log_level: str = Field(default="INFO")
    log_to_file: bool = Field(default=True)
    log_to_console: bool = Field(default=True)


def _parse_env_line(line: str) -> Optional[Tuple[str, str]]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export "):].strip()
    if "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None
    value = value.strip()
    if value and value[0] in {'"', "'"} and value[-1] == value[0]:
        value = value[1:-1]
    return key, value


def _load_env_fallback(env_path: Path) -> None:
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        parsed = _parse_env_line(line)
        if not parsed:
            continue
        key, value = parsed
        if key in os.environ:
            continue
        os.environ[key] = value


def _apply_env_overrides(config: Config) -> Config:
    """Update config paths from environment variables when provided."""
    data_dir = os.getenv("SINGLEFILE_DATA_DIR")
    if data_dir:
        config.project_dir = str(Path(data_dir).expanduser())

    archive_dir = os.getenv("SINGLEFILE_ARCHIVE_DIR")
    if archive_dir:
        archive_path = str(Path(archive_dir).expanduser())
        config.archive_output_dir = archive_path
        config.monitor_archive_dir = archive_path

    incoming_dir = os.getenv("SINGLEFILE_INCOMING_DIR")
    if incoming_dir:
        config.monitor_watch_dir = str(Path(incoming_dir).expanduser())

    return config


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration from file or create default."""
    project_dir = get_project_dir()
    project_root = project_dir.parent

    # Load environment variables from .env file if it exists
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            _load_env_fallback(env_file)

    if config_file is None:
        config_file = project_dir / "config.json"

    if config_file.exists():
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            return _apply_env_overrides(Config(**config_data))
        except (json.JSONDecodeError, Exception):
            # If config is corrupted, create a new one
            pass

    # Create default config
    config = _apply_env_overrides(Config())
    save_config(config, config_file)
    return config


def save_config(config: Config, config_file: Optional[Path] = None) -> None:
    """Save configuration to file."""
    if config_file is None:
        project_dir = get_project_dir()
        config_file = project_dir / "config.json"

    # Ensure parent directory exists
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w') as f:
        json.dump(config.model_dump(), f, indent=2)


def get_config() -> Config:
    """Get the current configuration."""
    return load_config()


def update_config(updates: Dict[str, Any]) -> Config:
    """Update configuration with new values."""
    config = get_config()

    # Update fields
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Save updated config
    save_config(config)
    return config
