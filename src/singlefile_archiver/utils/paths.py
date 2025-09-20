"""Path utilities and project directory management."""

import re
from pathlib import Path
from typing import Union


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


def get_project_dir(project_name: str = "singlefile-archiver") -> Path:
    """Get the project data directory using the current project root."""
    # Find the project root by looking for pyproject.toml
    current_dir = Path(__file__).parent
    while current_dir != current_dir.parent:
        if (current_dir / "pyproject.toml").exists():
            break
        current_dir = current_dir.parent
    else:
        # Fallback to current file's directory structure
        current_dir = Path(__file__).parent.parent.parent.parent
    
    # Create data directory in project root
    project_dir = current_dir / "data"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    return project_dir


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_archive_base_dir() -> Path:
    """Get the base directory for archived files."""
    project_dir = get_project_dir()
    archive_dir = project_dir / "archives"
    return ensure_directory(archive_dir)


def get_temp_dir() -> Path:
    """Get a temporary directory for processing."""
    project_dir = get_project_dir()
    temp_dir = project_dir / "temp"
    return ensure_directory(temp_dir)


def safe_filename(filename: str, max_length: int = 255) -> str:
    """Convert a string to a safe filename."""
    # Remove/replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'\s+', '_', safe_name)
    
    # Limit length
    if len(safe_name) > max_length:
        name_part = safe_name[:max_length-10]
        safe_name = f"{name_part}_{hash(filename) % 10000}"
    
    return safe_name