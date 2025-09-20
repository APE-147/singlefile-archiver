"""Logging configuration and utilities."""

import logging
import sys
from pathlib import Path
from typing import Optional

from .paths import get_project_dir


def setup_logging(
    name: Optional[str] = None,
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """Set up logging with file and console handlers."""
    logger = logging.getLogger(name or "singlefile_archiver")
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        project_dir = get_project_dir()
        log_file = project_dir / "logs" / "singlefile_archiver.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance."""
    return setup_logging(name)