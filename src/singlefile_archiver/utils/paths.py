"""Path utilities and project directory management."""

import re
import unicodedata
from pathlib import Path
from typing import Union
from urllib.parse import quote


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


def remove_emoji(text: str) -> str:
    """Remove emoji and problematic Unicode characters from text.
    
    Args:
        text: Input text that may contain emoji
        
    Returns:
        Text with emoji characters removed
    """
    if not text:
        return text

    # Define emoji ranges more comprehensively
    emoji_ranges = [
        # Main emoji blocks
        ('\U0001F600', '\U0001F64F'),  # Emoticons
        ('\U0001F300', '\U0001F5FF'),  # Miscellaneous Symbols and Pictographs
        ('\U0001F680', '\U0001F6FF'),  # Transport and Map Symbols
        ('\U0001F1E0', '\U0001F1FF'),  # Regional Indicator Symbols
        ('\U0001F700', '\U0001F77F'),  # Alchemical Symbols
        ('\U0001F780', '\U0001F7FF'),  # Geometric Shapes Extended
        ('\U0001F800', '\U0001F8FF'),  # Supplemental Arrows-C
        ('\U0001F900', '\U0001F9FF'),  # Supplemental Symbols and Pictographs
        ('\U0001FA00', '\U0001FA6F'),  # Chess Symbols
        ('\U0001FA70', '\U0001FAFF'),  # Symbols and Pictographs Extended-A
        ('\U00002600', '\U000026FF'),  # Miscellaneous Symbols
        ('\U00002700', '\U000027BF'),  # Dingbats
        ('\U0000FE00', '\U0000FE0F'),  # Variation Selectors
        ('\U0001F000', '\U0001F02F'),  # Mahjong Tiles
        ('\U0001F0A0', '\U0001F0FF'),  # Playing Cards
    ]

    result = []
    for char in text:
        # Check if character is in any emoji range
        is_emoji = False
        for start, end in emoji_ranges:
            if start <= char <= end:
                is_emoji = True
                break

        # Skip emoji characters
        if is_emoji:
            continue

        # Check Unicode categories for symbols that might be emoji
        category = unicodedata.category(char)
        if category in ('So', 'Sk'):
            # More specific filtering for symbols
            char_name = unicodedata.name(char, '').lower()
            if any(keyword in char_name for keyword in [
                'emoji', 'face', 'heart', 'star', 'fire', 'sun', 'moon',
                'balloon', 'party', 'celebration', 'thermometer', 'bug'
            ]):
                continue

        # Preserve most characters including useful symbols like °
        result.append(char)

    # Clean up extra whitespace
    clean_text = ''.join(result)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text


def optimize_filename(title: str, max_length: int = 120) -> str:
    """Optimize a filename by removing emoji and controlling length.
    
    Args:
        title: Original title/filename
        max_length: Maximum length for the optimized filename
        
    Returns:
        Optimized filename with emoji removed and length controlled
    """
    if not title:
        return "untitled"

    # Remove emoji and problematic characters
    clean_title = remove_emoji(title)

    # If title is empty after emoji removal, use a fallback
    if not clean_title.strip():
        return "untitled"

    # Normalize whitespace and basic cleanup
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()

    # If still within length limit, return as-is
    if len(clean_title) <= max_length:
        return clean_title

    # Intelligent truncation at word boundary
    if max_length <= 3:
        return clean_title[:max_length]

    # Try to break at a word boundary
    truncate_pos = max_length - 3  # Reserve space for "..."

    # Find the last space before the truncation point
    last_space = clean_title.rfind(' ', 0, truncate_pos)

    if last_space > max_length // 2:  # Only use word boundary if it's reasonable
        return clean_title[:last_space] + "..."
    else:
        return clean_title[:truncate_pos] + "..."


def encode_url_for_filename(url: str, max_length: int = 180) -> str:
    """Encode URL for safe inclusion in filename.
    
    Args:
        url: URL to encode
        max_length: Maximum length for encoded URL
        
    Returns:
        URL-encoded string safe for filenames
    """
    if not url:
        return "no-url"

    encoded = quote(url, safe="")
    if len(encoded) <= max_length:
        return encoded

    # Truncate with ellipsis
    return encoded[:max_length - 3] + "..."


def build_canonical_basename(title: str, url: str, max_title_length: int = 120) -> str:
    """Build a canonical basename for archived files.
    
    Args:
        title: Page title
        url: Source URL
        max_title_length: Maximum length for the title portion
        
    Returns:
        Canonical basename without extension
    """
    # Optimize the title (removes emoji and controls length)
    optimized_title = optimize_filename(title, max_title_length)

    # Encode URL for filename
    url_part = encode_url_for_filename(url, 60)  # Shorter URL part to save space

    # Build the canonical format: (title) [URL] encoded_url
    basename = f"({optimized_title}) [URL] {url_part}"

    return basename


def safe_filename(filename: str, max_length: int = 255) -> str:
    """Convert a string to a safe filename.
    
    Args:
        filename: Input filename
        max_length: Maximum length for the safe filename
        
    Returns:
        Filesystem-safe filename
    """
    if not filename:
        return "untitled"

    # Remove/replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'\s+', '_', safe_name)

    # Limit length
    if len(safe_name) > max_length:
        # Calculate stable hash for uniqueness
        hash_suffix = f"_{abs(hash(filename)) % 10000:04d}"
        max_base_length = max_length - len(hash_suffix)

        if max_base_length > 0:
            safe_name = safe_name[:max_base_length] + hash_suffix
        else:
            safe_name = f"file_{abs(hash(filename)) % 10000:04d}"

    return safe_name
