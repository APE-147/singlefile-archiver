"""Configuration management."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

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


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration from file or create default."""
    # Load environment variables from .env file if it exists
    from pathlib import Path
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # python-dotenv not available, skip loading .env file
            pass
    
    if config_file is None:
        project_dir = get_project_dir()
        config_file = project_dir / "config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            return Config(**config_data)
        except (json.JSONDecodeError, Exception):
            # If config is corrupted, create a new one
            pass
    
    # Create default config
    config = Config()
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
