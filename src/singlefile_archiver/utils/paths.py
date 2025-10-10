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


def _generate_fallback_name(base_name: str, existing_names: set = None) -> str:
    """Generate a unique fallback name when title is empty or invalid.
    
    Args:
        base_name: Base name to use (e.g., 'untitled')
        existing_names: Set of existing names to avoid
        
    Returns:
        Unique fallback name
    """
    if existing_names is None:
        existing_names = set()
    
    existing_lower = {name.lower() for name in existing_names}
    
    if base_name.lower() not in existing_lower:
        return base_name
        
    # Try numbered variations
    for i in range(1, 1000):
        candidate = f"{base_name}_{i}"
        if candidate.lower() not in existing_lower:
            return candidate
    
    # Last resort - use timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}"


def optimize_filename(title: str, max_length: int = 120, existing_names: set = None) -> str:
    """Optimize a filename by removing emoji and controlling length while ensuring uniqueness.
    
    Args:
        title: Original title/filename
        max_length: Maximum length for the optimized filename
        existing_names: Set of existing filenames to avoid duplicates
        
    Returns:
        Optimized filename with emoji removed, length controlled, and uniqueness ensured
    """
    if not title:
        return _generate_fallback_name("untitled", existing_names)

    # Remove emoji and problematic characters
    clean_title = remove_emoji(title)

    # If title is empty after emoji removal, use a fallback
    if not clean_title.strip():
        return _generate_fallback_name("untitled", existing_names)

    # Normalize whitespace and basic cleanup
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()

    # If still within length limit and unique, return as-is
    if len(clean_title) <= max_length:
        if existing_names is None or clean_title.lower() not in existing_names:
            return clean_title

    # Progressive truncation strategy to maintain uniqueness
    return _progressive_truncate_with_uniqueness(clean_title, max_length, existing_names)


def _progressive_truncate_with_uniqueness(title: str, max_length: int, existing_names: set = None) -> str:
    """Apply progressive truncation to maintain uniqueness while optimizing length.
    
    Args:
        title: Clean title to truncate
        max_length: Maximum allowed length
        existing_names: Set of existing names to avoid conflicts
        
    Returns:
        Truncated title that doesn't conflict with existing names
    """
    if existing_names is None:
        existing_names = set()

    # Handle very short max_length cases
    if max_length <= 3:
        candidate = title[:max_length]
        if candidate.lower() not in {name.lower() for name in existing_names}:
            return candidate
        # If even the short version conflicts, add a number
        for i in range(1, 10):
            if max_length > 1:
                numbered = title[:max_length-1] + str(i)
                if numbered.lower() not in {name.lower() for name in existing_names}:
                    return numbered
        return title[:max_length]  # Fallback

    # Convert existing names to lowercase for case-insensitive comparison
    existing_lower = {name.lower() for name in existing_names}

    # If no truncation needed and no conflict, return as-is
    if len(title) <= max_length and title.lower() not in existing_lower:
        return title

    # For very short limits, use simple truncation with numbering
    if max_length <= 10:
        base = title[:max_length-2] if max_length > 2 else title[:max_length]
        for i in range(1, 100):
            if max_length > 2:
                candidate = f"{base}{i:02d}"
            else:
                candidate = f"{base}{i}"
            if len(candidate) <= max_length and candidate.lower() not in existing_lower:
                return candidate
        return title[:max_length]  # Fallback

    # Try different truncation lengths, starting from max and working down
    # Only if we need to truncate due to length or conflict
    min_meaningful_length = max(max_length // 3, 15)  # Keep at least 1/3 or 15 chars

    for attempt_length in range(max_length - 3, min_meaningful_length - 1, -5):
        # Find good word boundary for truncation
        truncate_pos = attempt_length
        
        # Try to break at word boundary within reasonable range
        last_space = title.rfind(' ', attempt_length - 10, attempt_length)
        if last_space > max(attempt_length - 15, attempt_length // 2):
            truncate_pos = last_space

        candidate = title[:truncate_pos] + "..."
        
        # Check if this candidate is unique
        if candidate.lower() not in existing_lower:
            return candidate

    # If all attempts fail, create a unique name with hash suffix
    import hashlib
    title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:6]
    
    # Calculate how much space we have for the base
    hash_suffix = f"...{title_hash}"
    base_length = max_length - len(hash_suffix)
    
    if base_length <= 0:
        # Very short limit, just use hash
        return title_hash[:max_length]
    
    base = title[:base_length]
    final_result = f"{base}{hash_suffix}"
    
    # Double-check length constraint
    if len(final_result) > max_length:
        base = title[:max(max_length - len(hash_suffix), 1)]
        final_result = f"{base}{hash_suffix}"
    
    return final_result


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


def build_canonical_basename(title: str, url: str, max_title_length: int = 120, existing_names: set = None) -> str:
    """Build a canonical basename for archived files with deduplication.
    
    Args:
        title: Page title
        url: Source URL
        max_title_length: Maximum length for the title portion
        existing_names: Set of existing basenames to avoid duplicates
        
    Returns:
        Canonical basename without extension that's unique
    """
    # Optimize the title with deduplication (removes emoji and controls length)
    optimized_title = optimize_filename(title, max_title_length, existing_names)

    # Encode URL for filename - keep URL portion consistent
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
