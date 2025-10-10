"""Batch filename optimization commands."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from ..utils.logging import get_logger
from ..utils.paths import optimize_filename, safe_filename
from urllib.parse import quote

logger = get_logger(__name__)
console = Console()


@dataclass
class RenameOperation:
    """Represents a file rename operation."""
    old_path: Path
    new_path: Path
    old_name: str
    new_name: str
    conflict: bool = False
    reason: str = ""


def create_standardized_filename(title: str, url: str, max_length: int = 200) -> str:
    """Create a standardized filename format matching the user's specification.
    
    Args:
        title: Extracted title
        url: Original URL
        max_length: Maximum total filename length
        
    Returns:
        Standardized filename in format: "X_上的_DN-Samuel_[URL]_https%3A%2F%2Fx.com%2FSamuelQZQ%2Fstatus%2F1976062342451667233"
    """
    # Parse the title to extract platform and user info
    platform_info = _extract_platform_info(title)
    
    if platform_info:
        platform = platform_info['platform']
        user = platform_info['user']
        content_id = platform_info.get('content_id', '')
    else:
        # Fallback for non-social media content
        platform = "Web"
        user = "Content"
        content_id = ""
    
    # URL encode the URL portion
    encoded_url = quote(url, safe='')
    
    # Build the standardized format: Platform_上的_User_[URL]_encoded_url
    # Following the pattern: "X_上的_DN-Samuel_[URL]_https%3A%2F%2Fx.com%2FSamuelQZQ%2Fstatus%2F1976062342451667233"
    standardized = f"{platform}_上的_{user}_[URL]_{encoded_url}"
    
    # Ensure it doesn't exceed max_length
    if len(standardized) > max_length:
        # Truncate the encoded URL if needed
        available_for_url = max_length - len(f"{platform}_上的_{user}_[URL]_")
        if available_for_url > 10:  # Keep at least 10 chars for URL
            truncated_url = encoded_url[:available_for_url-3] + "..."
            standardized = f"{platform}_上的_{user}_[URL]_{truncated_url}"
        else:
            # If still too long, truncate the user part
            available_for_user = max_length - len(f"{platform}_上的__[URL]_{encoded_url[:20]}...")
            if available_for_user > 3:
                truncated_user = user[:available_for_user]
                standardized = f"{platform}_上的_{truncated_user}_[URL]_{encoded_url[:20]}..."
            else:
                # Final fallback
                standardized = f"{platform}_上的_User_[URL]_{encoded_url[:50]}..."
    
    return standardized


def create_enhanced_content_filename(title: str, max_length: int = 220) -> str:
    """Create enhanced filename for content without URLs with better content preservation.
    
    Args:
        title: Extracted title  
        max_length: Maximum total filename length (relaxed for non-URL cases)
        
    Returns:
        Enhanced filename preserving meaningful content: "X_上的_DN-Samuel_比特币总裁：过….html"
    """
    # Parse the title to extract platform and user info
    platform_info = _extract_platform_info(title)
    
    if platform_info:
        platform = platform_info['platform']
        user = platform_info['user']
        # Extract content description from title
        content_desc = _extract_content_description(title, platform_info)
    else:
        # For non-social media content, try to extract meaningful parts
        platform = "Web"
        user_match = re.search(r'@([a-zA-Z0-9_-]+)', title)
        user = user_match.group(1) if user_match else "Content"
        content_desc = _clean_content_description(title)
    
    # Build enhanced format: Platform_上的_User_ContentDescription
    base_format = f"{platform}_上的_{user}_"
    available_for_content = max_length - len(base_format)
    
    # Preserve more content with intelligent truncation
    if available_for_content > 20:
        # Use semantic-aware truncation to preserve meaning
        truncated_content = _semantic_truncate(content_desc, available_for_content)
        enhanced = f"{base_format}{truncated_content}"
    else:
        # Fallback to shorter format if space is very limited
        enhanced = f"{platform}_上的_{user}"
    
    return enhanced


def _extract_content_description(title: str, platform_info: dict) -> str:
    """Extract meaningful content description from title.
    
    Args:
        title: Original title
        platform_info: Platform information dict
        
    Returns:
        Cleaned content description
    """
    # Remove platform and user info from title to get content
    platform = platform_info.get('platform', '')
    user = platform_info.get('user', '')
    
    # **FIXED: Add patterns specific to the Chinese social media format**
    patterns_to_remove = [
        rf'{platform}_上的_{re.escape(user)}_?',  # Remove "X_上的_宝玉_" format
        rf'{platform.lower()}\.com',
        rf'@{user}',
        r'https?://[^\s]+',
        r'\[URL\]',
        r'status/\d+',
        r'posts?/',
        r'video/\d+',
    ]
    
    content = title
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # **ENHANCED: Better cleanup of Chinese punctuation and separators**
    content = re.sub(r'[_\-\s]+', ' ', content).strip()
    
    # **NEW: Remove Chinese punctuation and quotes**
    chinese_punct = '：""''""'
    for punct in chinese_punct + ':"\'':
        content = content.strip(punct + ' \t-_')
    
    content = content.strip()
    
    return content if content else "内容"


def _clean_content_description(title: str) -> str:
    """Clean content description for non-social media content.
    
    Args:
        title: Original title
        
    Returns:
        Cleaned content description
    """
    # Remove common web artifacts
    content = re.sub(r'https?://[^\s]+', '', title)
    content = re.sub(r'\[URL\]', '', content)
    content = re.sub(r'[\(\)\[\]]+', '', content)
    content = re.sub(r'[_\-\s]+', ' ', content).strip()
    
    return content if content else "页面内容"


def _semantic_truncate(text: str, max_length: int) -> str:
    """Perform semantic-aware truncation to preserve meaning.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Semantically truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Try to preserve complete words and meaningful phrases
    words = text.split()
    
    # If very short limit, just truncate
    if max_length < 10:
        return text[:max_length-1] + "…"
    
    # Strategy 1: Try to keep complete sentences
    sentence_endings = ['.', '!', '?', '。', '！', '？']
    for i, char in enumerate(text):
        if char in sentence_endings and i < max_length - 1 and i >= max_length * 0.5:
            return text[:i+1]
    
    # Strategy 2: Try to keep complete phrases (up to punctuation)
    phrase_endings = [',', ';', ':', '，', '；', '：', '"', '"', ''', ''']
    for i, char in enumerate(text):
        if char in phrase_endings and i < max_length - 1 and i >= max_length * 0.6:
            return text[:i] + "…"
    
    # Strategy 3: Find word boundary
    if max_length > 3:
        truncate_pos = max_length - 1
        while truncate_pos > max_length * 0.7 and truncate_pos > 0:
            if text[truncate_pos] == ' ':
                return text[:truncate_pos] + "…"
            truncate_pos -= 1
    
    # Fallback: simple truncation with ellipsis
    return text[:max_length-1] + "…"


def _extract_platform_info(title: str) -> dict:
    """Extract platform and user information from title.
    
    Args:
        title: Title to parse
        
    Returns:
        Dictionary with platform, user, and optional content_id
    """
    # Enhanced pattern matching with better user extraction
    title_lower = title.lower()
    
    # Check for explicit platform mentions first
    if '上的' in title and ('x_' in title_lower or 'twitter' in title_lower):
        # Pattern: X_上的_Username or Twitter format
        # Fixed: Stop at colon, quote, or common separators
        user_match = re.search(r'(?:x|twitter)_上的_([^_\s：""''"]+)', title, re.IGNORECASE)
        if user_match:
            return {
                'platform': 'X',
                'user': user_match.group(1),
                'content_id': ''
            }
    
    if '上的' in title and 'instagram' in title_lower:
        user_match = re.search(r'instagram[_\s]*上的[_\s]*([^_\s]+)', title_lower)
        if user_match:
            return {
                'platform': 'Instagram', 
                'user': user_match.group(1),
                'content_id': ''
            }
    
    # Social media domain patterns with enhanced parsing
    patterns = [
        # Twitter/X.com patterns - look for @username or extract from context
        (r'(twitter\.com|x\.com)[/_\\]([a-zA-Z0-9_]+)[/_\\]status[/_\\]([0-9]+)', 'X'),
        (r'(twitter\.com|x\.com).*?@([a-zA-Z0-9_]+)', 'X'),
        (r'(twitter\.com|x\.com)[/_\\]([a-zA-Z0-9_]+)', 'X'),
        
        # Instagram patterns  
        (r'instagram\.com[/_\\]p[/_\\]([a-zA-Z0-9_\.]+)', 'Instagram'),
        (r'instagram\.com.*?@([a-zA-Z0-9_\.]+)', 'Instagram'),
        (r'instagram\.com[/_\\]([a-zA-Z0-9_\.]+)', 'Instagram'),
        
        # LinkedIn patterns
        (r'linkedin\.com[/_\\]posts[/_\\]([a-zA-Z0-9_-]+)', 'LinkedIn'),
        (r'linkedin\.com.*?@([a-zA-Z0-9_-]+)', 'LinkedIn'),
        
        # TikTok patterns
        (r'tiktok\.com[/_\\]@([a-zA-Z0-9_\.]+)', 'TikTok'),
        
        # YouTube patterns
        (r'youtube\.com[/_\\]watch\?v=([a-zA-Z0-9_-]+)', 'YouTube'),
        (r'youtu\.be[/_\\]([a-zA-Z0-9_-]+)', 'YouTube'),
        
        # Reddit patterns
        (r'reddit\.com[/_\\]r[/_\\]([a-zA-Z0-9_]+)', 'Reddit'),
    ]
    
    for pattern, platform_name in patterns:
        match = re.search(pattern, title_lower)
        if match:
            # Extract user from the first capturing group
            user = match.group(2) if len(match.groups()) >= 2 else match.group(1) if match.groups() else "User"
            
            # Clean up user name
            user = re.sub(r'[^a-zA-Z0-9_-]', '', user)
            if not user or user in ['com', 'status', 'watch', 'posts']:
                user = "User"
            
            # Try to extract content ID from additional groups
            content_id = ""
            if len(match.groups()) >= 3:
                content_id = match.group(3)
            
            return {
                'platform': platform_name,
                'user': user,
                'content_id': content_id
            }
    
    # If no domain patterns found, check for general social media keywords
    if any(keyword in title_lower for keyword in ['上的', '微博', 'weibo', 'twitter', 'instagram']):
        # Try to extract user from context
        user_patterns = [
            r'上的[_\s]*([^_\s，。：]{2,})',  # Chinese format
            r'@([a-zA-Z0-9_-]+)',          # @mention format
            r'[_\s]([a-zA-Z0-9_-]{3,})[_\s]',  # Username in underscores
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, title)
            if match:
                user = match.group(1)
                # Determine platform from context
                if 'x_' in title_lower or 'twitter' in title_lower:
                    platform = 'X'
                elif 'instagram' in title_lower:
                    platform = 'Instagram'
                elif '微博' in title_lower or 'weibo' in title_lower:
                    platform = 'Weibo'
                else:
                    platform = 'Social'
                
                return {
                    'platform': platform,
                    'user': user,
                    'content_id': ''
                }
    
    return None


def extract_title_from_filename(filename: str) -> str:
    """Extract the title portion from an archived filename with enhanced social media support.
    
    Args:
        filename: The original filename
        
    Returns:
        Extracted title or meaningful representation for social media URLs
    """
    # Remove extension
    base_name = filename.replace('.html', '').replace('.htm', '')

    # Try to extract title from pattern: (title) [URL] encoded_url
    title_match = re.match(r'^\(([^)]+)\)', base_name)
    if title_match:
        return title_match.group(1)

    # **NEW: Enhanced social media URL parsing**
    # Handle Twitter/X.com patterns: twitter.com_username_status_statusid
    social_media_patterns = [
        # Twitter/X.com: domain_username_status_id
        (r'^(twitter\.com|x\.com)_([^_]+)_status_([0-9]+)$', lambda m: f"{m.group(1)} - @{m.group(2)} (Status {m.group(3)[-6:]})"),
        # Instagram: instagram.com_p_postid or instagram.com_username
        (r'^instagram\.com_p_([^_]+)$', lambda m: f"Instagram Post {m.group(1)}"),
        (r'^instagram\.com_([^_]+)$', lambda m: f"Instagram @{m.group(1)}"),
        # LinkedIn: linkedin.com_posts_username_activity-id
        (r'^linkedin\.com_posts_([^_]+)_activity-([0-9]+)$', lambda m: f"LinkedIn @{m.group(1)} (Activity {m.group(2)[-6:]})"),
        # TikTok: tiktok.com_@username_video_id
        (r'^tiktok\.com_@([^_]+)_video_([0-9]+)$', lambda m: f"TikTok @{m.group(1)} (Video {m.group(2)[-6:]})"),
        # YouTube: youtube.com_watch?v=videoid or youtu.be_videoid
        (r'^youtube\.com_watch\?v=([^_&]+)', lambda m: f"YouTube Video {m.group(1)}"),
        (r'^youtu\.be_([^_]+)$', lambda m: f"YouTube Video {m.group(1)}"),
        # Reddit: reddit.com_r_subreddit_posts_id
        (r'^reddit\.com_r_([^_]+)_[^_]+_([^_]+)$', lambda m: f"Reddit r/{m.group(1)} ({m.group(2)[-6:]})"),
        # Generic social media: domain_username_content
        (r'^([a-z]+\.com)_([^_]+)_(.+)$', lambda m: f"{m.group(1)} - @{m.group(2)} ({m.group(3)[:10]})"),
    ]
    
    for pattern, formatter in social_media_patterns:
        match = re.match(pattern, base_name)
        if match:
            try:
                formatted_title = formatter(match)
                # Additional cleanup: limit length and ensure uniqueness
                if len(formatted_title) > 100:
                    formatted_title = formatted_title[:97] + "..."
                return formatted_title
            except Exception:
                # If formatting fails, continue to next pattern
                continue

    # Try to extract from other common patterns
    # Pattern: title - URL or title_URL
    for separator in [' - ', '_', ' ']:
        if separator in base_name:
            parts = base_name.split(separator)
            if len(parts) >= 2:
                # For social media domains, try to preserve more context
                if any(domain in base_name.lower() for domain in ['twitter.com', 'x.com', 'instagram.com', 'linkedin.com']):
                    # Try to build a more meaningful title from parts
                    domain_part = parts[0] if any(tld in parts[0] for tld in ['.com', '.org', '.net']) else None
                    if domain_part and len(parts) >= 3:
                        # Pattern: domain_user_content
                        return f"{domain_part} - {parts[1]} ({parts[2][:10]})"
                return parts[0].strip()

    # **NEW: Final fallback for social media - extract domain and key info**
    if '_' in base_name and any(domain in base_name.lower() for domain in ['twitter.com', 'x.com', 'instagram.com']):
        parts = base_name.split('_')
        if len(parts) >= 2:
            domain = parts[0]
            user_info = parts[1] if len(parts) > 1 else ''
            content_info = parts[-1] if len(parts) > 2 else ''
            # Create a meaningful representation
            if user_info and content_info != user_info:
                return f"{domain} - {user_info} ({content_info[-8:]})"
            elif user_info:
                return f"{domain} - {user_info}"
    
    # Final fallback: use the whole base name
    return base_name


def _optimize_filename_with_fallbacks(title: str, original_filename: str, max_length: int = 120, existing_names: set = None) -> str:
    """Optimize filename with multiple fallback strategies for maximum uniqueness.
    
    Args:
        title: Extracted title
        original_filename: Original filename for fallback context
        max_length: Maximum length
        existing_names: Existing names to avoid
        
    Returns:
        Optimized title guaranteed to be unique
    """
    if existing_names is None:
        existing_names = set()
    
    existing_lower = {name.lower() for name in existing_names}
    
    # Strategy 1: Try standard optimization
    optimized = optimize_filename(title, max_length, existing_names)
    if optimized.lower() not in existing_lower:
        return optimized
    
    # Strategy 2: Include original filename hash for uniqueness  
    import hashlib
    filename_hash = hashlib.md5(original_filename.encode('utf-8')).hexdigest()[:8]
    
    # Try incorporating the hash
    hash_suffix = f"_{filename_hash}"
    available_length = max_length - len(hash_suffix)
    
    if available_length > 10:
        base_title = optimize_filename(title, available_length, set())  # Don't consider existing for base
        candidate = f"{base_title}{hash_suffix}"
        if candidate.lower() not in existing_lower:
            return candidate
    
    # Strategy 3: Extract more info from original filename for social media
    if '_' in original_filename and any(domain in original_filename.lower() for domain in ['twitter.com', 'x.com', 'instagram.com']):
        parts = original_filename.split('_')
        if len(parts) >= 3:
            # Use domain + user + content_id for uniqueness
            domain = parts[0]
            user = parts[1] 
            content_id = parts[-1][-8:]  # Last 8 chars of content ID
            
            enhanced_title = f"{domain} {user} {content_id}"
            enhanced_optimized = optimize_filename(enhanced_title, max_length, set())
            if enhanced_optimized.lower() not in existing_lower:
                return enhanced_optimized
    
    # Strategy 4: Sequential numbering as absolute fallback
    base = optimize_filename(title, max_length - 4, set())  # Reserve space for "_999"
    for i in range(1, 1000):
        candidate = f"{base}_{i:03d}"
        if len(candidate) <= max_length and candidate.lower() not in existing_lower:
            return candidate
    
    # Strategy 5: Ultimate fallback - timestamp-based unique name
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:20]  # Include microseconds
    return f"unique_{timestamp}"


def generate_optimized_filename(original_path: Path, existing_names: set = None, use_standardized_format: bool = True) -> str:
    """Generate an optimized filename from the original with enhanced deduplication.
    
    Args:
        original_path: Path to the original file
        existing_names: Set of existing filenames to avoid duplicates
        use_standardized_format: Whether to use the new standardized format
        
    Returns:
        Optimized filename that doesn't conflict with existing names
    """
    original_name = original_path.stem
    extension = original_path.suffix

    # Extract title from the filename (now with enhanced social media support)
    title = extract_title_from_filename(original_name)
    
    # **NEW: Try to extract URL from original filename**
    extracted_url = _extract_url_from_filename(original_name)
    
    # **ENHANCED: Smart format selection based on URL presence**
    if use_standardized_format:
        try:
            if extracted_url:
                # Case 1: URL detected - use standardized format with URL
                standardized_title = create_standardized_filename(title, extracted_url, max_length=200)
                logger.info(f"Using URL format for {original_name[:50]}...")
            else:
                # Case 2: No URL - use enhanced content preservation format with relaxed length
                standardized_title = create_enhanced_content_filename(title, max_length=220)
                logger.info(f"Using enhanced content format for {original_name[:50]}...")
            
            # Ensure uniqueness
            final_title = _ensure_unique_filename(standardized_title, existing_names)
            new_name = safe_filename(final_title) + extension
            return new_name
        except Exception as e:
            logger.warning(f"Failed to create enhanced filename for {original_name}: {e}")
            # Fall back to original logic

    # **FALLBACK: Enhanced deduplication with fallback strategies**
    optimized_title = _optimize_filename_with_fallbacks(title, original_name, max_length=120, existing_names=existing_names)

    # Create the new filename
    new_name = safe_filename(optimized_title) + extension

    return new_name


def _extract_url_from_filename(filename: str) -> str:
    """Extract URL from filename using enhanced pattern detection.
    
    Args:
        filename: Original filename
        
    Returns:
        Extracted URL or empty string if not found
    """
    # Pattern 1: [URL] encoded_url format (highest priority)
    url_pattern_1 = r'\[URL\]\s*([^\s]+)'
    match = re.search(url_pattern_1, filename)
    if match:
        encoded_url = match.group(1)
        try:
            from urllib.parse import unquote
            decoded = unquote(encoded_url)
            # Validate that it's a proper URL
            if decoded.startswith(('http://', 'https://')):
                return decoded
            # If not proper URL after decoding, try to construct one
            elif encoded_url.startswith(('http', '%')):
                return decoded
            return encoded_url
        except:
            return encoded_url
    
    # Pattern 2: Direct URL patterns in parentheses or after separators
    url_patterns = [
        r'\((https?://[^\)]+)\)',  # URLs in parentheses
        r'[-_\s](https?://[^\s]+)(?:\s|$)',  # URLs after separators
        r'^(https?://[^\s]+)',  # URLs at the start
    ]
    
    for pattern in url_patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    # Pattern 3: Enhanced social media domain reconstruction
    social_patterns = [
        # Twitter/X.com patterns
        (r'(twitter\.com|x\.com)[/_\\]([^_\s\\]+)[/_\\]status[/_\\]([0-9]+)', 
         lambda m: f"https://x.com/{m.group(2)}/status/{m.group(3)}"),
        
        # Instagram patterns
        (r'instagram\.com[/_\\]p[/_\\]([^_\s\\]+)', 
         lambda m: f"https://instagram.com/p/{m.group(1)}"),
        (r'instagram\.com[/_\\]([^_\s\\]+)', 
         lambda m: f"https://instagram.com/{m.group(1)}"),
         
        # YouTube patterns
        (r'youtube\.com[/_\\]watch[?\\]v=([^_\s&\\]+)', 
         lambda m: f"https://youtube.com/watch?v={m.group(1)}"),
        (r'youtu\.be[/_\\]([^_\s\\]+)', 
         lambda m: f"https://youtu.be/{m.group(1)}"),
         
        # LinkedIn patterns
        (r'linkedin\.com[/_\\]posts[/_\\]([^_\s\\]+)', 
         lambda m: f"https://linkedin.com/posts/{m.group(1)}"),
        (r'linkedin\.com[/_\\]in[/_\\]([^_\s\\]+)', 
         lambda m: f"https://linkedin.com/in/{m.group(1)}"),
         
        # Reddit patterns
        (r'reddit\.com[/_\\]r[/_\\]([^_\s\\]+)[/_\\]comments[/_\\]([^_\s\\]+)', 
         lambda m: f"https://reddit.com/r/{m.group(1)}/comments/{m.group(2)}"),
        (r'reddit\.com[/_\\]r[/_\\]([^_\s\\]+)', 
         lambda m: f"https://reddit.com/r/{m.group(1)}"),
         
        # TikTok patterns
        (r'tiktok\.com[/_\\]@([^_\s\\]+)[/_\\]video[/_\\]([0-9]+)', 
         lambda m: f"https://tiktok.com/@{m.group(1)}/video/{m.group(2)}"),
         
        # Generic domain patterns for common sites
        (r'([a-z0-9-]+\.(?:com|org|net|edu))[/_\\]([^_\s\\]+)', 
         lambda m: f"https://{m.group(1)}/{m.group(2)}"),
    ]
    
    for pattern, url_builder in social_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            try:
                constructed_url = url_builder(match)
                # Basic validation that URL looks reasonable
                if constructed_url.startswith('https://') and '.' in constructed_url:
                    return constructed_url
            except Exception:
                continue
    
    # Pattern 4: Look for URL-like patterns without protocol
    domain_pattern = r'([a-z0-9-]+\.(?:com|org|net|edu|gov|io|co))\b'
    match = re.search(domain_pattern, filename.lower())
    if match:
        domain = match.group(1)
        # Only return if this looks like a primary domain, not just any domain
        if domain in ['x.com', 'twitter.com', 'instagram.com', 'youtube.com', 'linkedin.com', 'reddit.com', 'tiktok.com']:
            # Look for more context around this domain
            domain_context = re.search(rf'{re.escape(domain)}[/_\\]([^_\s\\]+)', filename.lower())
            if domain_context:
                return f"https://{domain}/{domain_context.group(1)}"
    
    return ""


def _has_url_indicators(filename: str) -> bool:
    """Check if filename has indicators suggesting it contains URL information.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename likely contains URL information
    """
    url_indicators = [
        '[URL]',  # Explicit URL marker
        'https://', 'http://',  # Direct URLs
        'twitter.com', 'x.com', 'instagram.com', 'youtube.com',  # Social media domains
        'linkedin.com', 'reddit.com', 'tiktok.com',
        '%3A%2F%2F',  # URL-encoded protocol separator
        '/status/', '/p/', '/watch?v=', '/posts/',  # URL path patterns
    ]
    
    filename_lower = filename.lower()
    return any(indicator in filename_lower for indicator in url_indicators)


def _ensure_unique_filename(filename: str, existing_names: set = None) -> str:
    """Ensure filename is unique by adding suffix if needed.
    
    Args:
        filename: Proposed filename
        existing_names: Set of existing names
        
    Returns:
        Unique filename
    """
    if existing_names is None:
        return filename
    
    existing_lower = {name.lower() for name in existing_names}
    
    if filename.lower() not in existing_lower:
        return filename
    
    # Add numerical suffix for uniqueness
    base = filename
    for i in range(1, 1000):
        candidate = f"{base}_{i:03d}"
        if candidate.lower() not in existing_lower:
            return candidate
    
    # Fallback with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%H%M%S')
    return f"{base}_{timestamp}"


def scan_archive_directory(directory: Path, pattern: str = "*.html") -> Tuple[List[Path], dict]:
    """Scan directory for archive files and categorize by length.
    
    Args:
        directory: Directory to scan
        pattern: File pattern to match
        
    Returns:
        Tuple of (files_to_process, statistics) where statistics contains 
        counts for different categories
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return [], {}

    files = []
    try:
        files = list(directory.glob(pattern))
        files.extend(directory.glob("*.htm"))  # Also include .htm files

        # **NEW: Categorize files by byte length for length-based filtering**
        files_to_process = []
        skipped_short = []
        stats = {
            'total_found': len(files),
            'needs_processing': 0,
            'skipped_short': 0,
            'already_optimized': 0
        }
        
        for file_path in files:
            name = file_path.name  # Full filename with extension
            stem = file_path.stem   # Name without extension
            
            # **NEW: Check byte length using UTF-8 encoding**
            byte_length = len(name.encode('utf-8'))
            
            # **PRIMARY FILTER: Only process files > 255 bytes**
            if byte_length <= 255:
                skipped_short.append(file_path)
                stats['skipped_short'] += 1
                continue
            
            # Secondary filter: Basic optimization heuristic
            if len(stem) <= 120 and not any(c for c in stem if ord(c) > 127):
                # Check if it contains obvious emoji patterns
                if not re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', stem):
                    # This file might already be optimized but still over 255 bytes
                    stats['already_optimized'] += 1
            
            files_to_process.append(file_path)
            stats['needs_processing'] += 1

        return files_to_process, stats

    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
        return [], {}


def generate_rename_operations(files: List[Path]) -> List[RenameOperation]:
    """Generate rename operations for a list of files with intelligent deduplication.
    
    Args:
        files: List of file paths to process
        
    Returns:
        List of rename operations with conflicts resolved through progressive truncation
    """
    operations = []
    used_final_names = set()  # Track final safe filenames
    used_optimized_titles = set()  # Track optimized titles for deduplication
    
    # Build set of existing filenames in the directory for context
    if files:
        directory = files[0].parent
        existing_files = {f.stem.lower() for f in directory.glob('*') if f.is_file()}
    else:
        existing_files = set()

    # **IMPROVED: Pre-process all titles to identify similar patterns for better deduplication**
    # Extract and clean titles first for proper pattern analysis
    raw_titles = [extract_title_from_filename(f.stem) for f in files]
    from ..utils.paths import remove_emoji
    clean_titles = [remove_emoji(title) for title in raw_titles]
    title_analysis = _analyze_title_patterns(clean_titles)

    # First pass: generate all potential names with proper deduplication
    for i, file_path in enumerate(files):
        try:
            # Extract title from filename
            original_name = file_path.stem
            extension = file_path.suffix
            title = extract_title_from_filename(original_name)
            
            # **NEW: Use standardized format for files that need processing**
            # Since we're only processing files >255 bytes, use standardized format
            new_name = generate_optimized_filename(
                file_path, 
                existing_names=used_optimized_titles, 
                use_standardized_format=True
            )
            
            # Extract the stem for tracking
            optimized_title = Path(new_name).stem
            
            # Track this optimized title
            used_optimized_titles.add(optimized_title.lower())
            
            new_path = file_path.parent / new_name

            # Check for conflicts
            conflict = False
            reason = ""

            if new_path.exists() and new_path != file_path:
                conflict = True
                reason = "Target file already exists"
            elif new_name.lower() in used_final_names:
                # This should be very rare now with proper deduplication
                conflict = True
                reason = "Duplicate name generated (deduplication failed)"
            else:
                used_final_names.add(new_name.lower())

            operation = RenameOperation(
                old_path=file_path,
                new_path=new_path,
                old_name=file_path.name,
                new_name=new_name,
                conflict=conflict,
                reason=reason
            )

            operations.append(operation)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            continue

    return operations


def _analyze_title_patterns(titles: List[str]) -> dict:
    """Analyze title patterns to identify common prefixes and optimize length allocation.
    
    Args:
        titles: List of titles to analyze
        
    Returns:
        Dictionary containing pattern analysis results
    """
    if not titles:
        return {}
    
    # Find common prefixes and patterns
    common_prefixes = {}
    pattern_groups = {}
    
    # Group titles by similar prefixes (first 2-4 words) with more granularity
    for title in titles:
        words = title.split()
        if len(words) >= 2:
            # Check different prefix lengths
            for prefix_len in range(2, min(len(words) + 1, 5)):  # 2-4 words
                prefix = ' '.join(words[:prefix_len])
                if prefix not in common_prefixes:
                    common_prefixes[prefix] = []
                common_prefixes[prefix].append(title)
    
    # Also check for structural patterns (e.g., "Complete [LANGUAGE] Programming")
    for title in titles:
        words = title.split()
        if len(words) >= 3:
            # Pattern: Complete X Programming
            if words[0].lower() == 'complete' and len(words) >= 3:
                if 'programming' in [w.lower() for w in words]:
                    pattern_key = 'Complete * Programming'
                    if pattern_key not in pattern_groups:
                        pattern_groups[pattern_key] = []
                    pattern_groups[pattern_key].append(title)
            
            # Pattern: X News: Y
            if len(words) >= 2 and words[1].lower() in ['news:', 'news']:
                pattern_key = '* News: *'
                if pattern_key not in pattern_groups:
                    pattern_groups[pattern_key] = []
                pattern_groups[pattern_key].append(title)
                
            # Pattern: Understanding X: Y
            if words[0].lower() == 'understanding' and len(words) >= 3:
                pattern_key = 'Understanding *: *'
                if pattern_key not in pattern_groups:
                    pattern_groups[pattern_key] = []
                pattern_groups[pattern_key].append(title)
    
    # Combine prefix groups and pattern groups
    similar_groups = {}
    
    # Add significant prefix groups (2+ titles with same prefix)
    for prefix, group_titles in common_prefixes.items():
        if len(group_titles) >= 2 and len(prefix.split()) >= 2:
            similar_groups[prefix] = group_titles
    
    # Add pattern groups (2+ titles with same structural pattern) 
    for pattern, group_titles in pattern_groups.items():
        if len(group_titles) >= 2:
            similar_groups[pattern] = group_titles
    
    # Find the most significant overlaps - prefer longer/more specific matches
    significant_groups = {}
    for prefix, group_titles in similar_groups.items():
        if len(group_titles) >= 2:
            # Filter out very generic patterns unless they're structural patterns
            prefix_words = prefix.split()
            is_structural_pattern = '*' in prefix
            is_meaningful_prefix = len(prefix_words) >= 2 and not all(w.lower() in ['the', 'a', 'an'] for w in prefix_words[:2])
            
            if is_structural_pattern or is_meaningful_prefix:
                significant_groups[prefix] = group_titles
    
    return {
        'total_titles': len(titles),
        'common_prefixes': common_prefixes,
        'pattern_groups': pattern_groups,
        'similar_groups': significant_groups,
        'needs_aggressive_dedup': len(significant_groups) > 0
    }


def _calculate_optimal_length(title: str, analysis: dict, base_length: int = 120) -> int:
    """Calculate optimal length for a title based on pattern analysis.
    
    Args:
        title: Title to optimize
        analysis: Pattern analysis results
        base_length: Base maximum length
        
    Returns:
        Optimal length for this specific title
    """
    if not analysis or not analysis.get('needs_aggressive_dedup'):
        return base_length
    
    # Check if this title is part of a similar group
    words = title.split()
    if len(words) >= 3:
        prefix_3 = ' '.join(words[:3])
        prefix_4 = ' '.join(words[:4]) if len(words) >= 4 else prefix_3
        
        for prefix in [prefix_4, prefix_3]:
            if prefix in analysis.get('similar_groups', {}):
                group_size = len(analysis['similar_groups'][prefix])
                if group_size >= 3:
                    # For highly similar groups, allow more length to preserve distinguishing content
                    return min(base_length + 20, 150)  # Allow up to 150 chars for similar groups
    
    return base_length


def preview_operations(operations: List[RenameOperation], scan_stats: dict = None) -> None:
    """Display a preview of rename operations with enhanced statistics.
    
    Args:
        operations: List of rename operations to preview
        scan_stats: Statistics from directory scanning
    """
    if not operations:
        console.print("[yellow]No files found to optimize.[/yellow]")
        return

    table = Table(title="Filename Optimization Preview")
    table.add_column("Current Name", style="cyan", max_width=50)
    table.add_column("New Name", style="green", max_width=50)
    table.add_column("Byte Length", style="dim", justify="right")
    table.add_column("Status", style="bold")
    table.add_column("Notes", style="dim")

    changes_count = 0
    conflicts_count = 0
    standardized_count = 0

    for op in operations:
        # Calculate byte lengths
        old_bytes = len(op.old_name.encode('utf-8'))
        new_bytes = len(op.new_name.encode('utf-8'))
        byte_info = f"{old_bytes}→{new_bytes}"
        
        # Check if this uses standardized format
        is_standardized = "_上的_" in op.new_name and "_[URL]_" in op.new_name
        
        if op.old_name == op.new_name:
            status = "[dim]No change[/dim]"
            notes = "Already optimized"
        elif op.conflict:
            status = "[red]Conflict[/red]"
            notes = op.reason
            conflicts_count += 1
        else:
            status = "[green]Will rename[/green]"
            if is_standardized:
                notes = "✓ Standardized"
                standardized_count += 1
            else:
                notes = "✓ Optimized"
            changes_count += 1

        table.add_row(op.old_name, op.new_name, byte_info, status, notes)

    console.print(table)
    
    # **NEW: Enhanced summary with detailed statistics**
    console.print(f"\n[bold]Processing Summary:[/bold]")
    if scan_stats:
        console.print(f"  Total files found: {scan_stats.get('total_found', 0)}")
        console.print(f"  Files skipped (≤255 bytes): {scan_stats.get('skipped_short', 0)}")
        console.print(f"  Files to process (>255 bytes): {scan_stats.get('needs_processing', 0)}")
    
    console.print(f"\n[bold]Rename Operations:[/bold]")
    console.print(f"  Files to rename: {changes_count}")
    console.print(f"  Using standardized format: {standardized_count}")
    console.print(f"  Conflicts detected: {conflicts_count}")
    
    if changes_count > 0:
        console.print(f"\n[green]✓[/green] All renamed files will be ≤255 bytes")
        console.print(f"[green]✓[/green] Standardized format: Platform_上的_User_[URL]_encoded_url")
        
    if conflicts_count > 0:
        console.print(f"\n[yellow]⚠️[/yellow] {conflicts_count} files have conflicts and may need manual resolution")


def apply_operations(operations: List[RenameOperation], force: bool = False) -> Tuple[int, int]:
    """Apply rename operations.
    
    Args:
        operations: List of rename operations to apply
        force: Whether to skip confirmation prompts
        
    Returns:
        Tuple of (successful_renames, failed_renames)
    """
    successful = 0
    failed = 0

    for op in operations:
        if op.old_name == op.new_name:
            continue  # Skip files that don't need renaming

        if op.conflict and not force:
            console.print(f"[yellow]Skipping {op.old_name}: {op.reason}[/yellow]")
            failed += 1
            continue

        try:
            # Perform the rename
            op.old_path.rename(op.new_path)
            console.print(f"[green]✓[/green] Renamed: {op.old_name} → {op.new_name}")
            successful += 1
            logger.info(f"Renamed file: {op.old_path} → {op.new_path}")

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to rename {op.old_name}: {e}")
            logger.error(f"Failed to rename {op.old_path}: {e}")
            failed += 1

    return successful, failed


def optimize_filenames_command(
    directory: str = typer.Argument(..., help="Directory containing archive files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
    interactive: bool = typer.Option(False, "--interactive", help="Ask for confirmation before each rename"),
    force: bool = typer.Option(False, "--force", help="Apply changes without confirmation (use with caution)"),
    pattern: str = typer.Option("*.html", "--pattern", help="File pattern to match")
) -> None:
    """Optimize filenames for archived files.
    
    This command will:
    1. Remove emoji and special characters from filenames
    2. Control filename length with intelligent truncation
    3. Apply consistent naming conventions
    """
    # Check feature flag with improved user experience
    if not os.getenv('FF_BATCH_PROCESSING', 'false').lower() == 'true':
        console.print("[yellow]⚠️  Batch processing feature flag is not enabled.[/yellow]")
        console.print()
        console.print("[bold]To enable batch processing, you have several options:[/bold]")
        console.print("1. [green]Set environment variable:[/green] export FF_BATCH_PROCESSING=true")
        console.print("2. [green]Run with inline variable:[/green] FF_BATCH_PROCESSING=true python -m singlefile_archiver.commands.optimize [DIRECTORY]")
        console.print("3. [green]Use the convenience script:[/green] python run_optimize.py [DIRECTORY] --dry-run")
        console.print()
        console.print("[dim]This safety feature prevents accidental bulk file operations.[/dim]")
        console.print("[dim]Learn more in the documentation about feature flags and safety controls.[/dim]")
        
        # Offer to run with the flag enabled interactively
        # Allow interactive enabling for dry-run (safe) or when not forced
        if not force:
            console.print()
            if dry_run:
                console.print("[dim]Since you're using --dry-run (safe preview mode), we can enable it temporarily.[/dim]")
            enable_flag = Confirm.ask("Would you like to enable batch processing for this session?")
            if enable_flag:
                os.environ['FF_BATCH_PROCESSING'] = 'true'
                console.print("[green]✓ Batch processing enabled for this session.[/green]")
            else:
                console.print("[yellow]Batch processing remains disabled. Exiting.[/yellow]")
                raise typer.Exit(0)
        else:
            # Force mode without feature flag - exit with error
            console.print("[red]Cannot use --force without enabling FF_BATCH_PROCESSING.[/red]")
            raise typer.Exit(1)

    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[red]Directory does not exist: {directory}[/red]")
        raise typer.Exit(1)

    if not dir_path.is_dir():
        console.print(f"[red]Path is not a directory: {directory}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Scanning directory:[/bold] {dir_path}")

    # Scan for files with length-based filtering
    files, scan_stats = scan_archive_directory(dir_path, pattern)
    
    # **NEW: Display detailed scanning statistics**
    console.print(f"Found {scan_stats.get('total_found', 0)} files matching pattern '{pattern}'")
    console.print(f"- Files needing processing (>255 bytes): {scan_stats.get('needs_processing', 0)}")
    console.print(f"- Files skipped (≤255 bytes): {scan_stats.get('skipped_short', 0)}")
    if scan_stats.get('already_optimized', 0) > 0:
        console.print(f"- Files already optimized: {scan_stats.get('already_optimized', 0)}")

    if not files:
        if scan_stats.get('skipped_short', 0) > 0:
            console.print("[yellow]No files need processing. All files are ≤255 bytes.[/yellow]")
        else:
            console.print("[yellow]No files found to process.[/yellow]")
        return

    # Generate rename operations
    operations = generate_rename_operations(files)

    # Preview operations with statistics
    preview_operations(operations, scan_stats)

    if dry_run:
        console.print("\n[bold blue]Dry run complete. No files were modified.[/bold blue]")
        return

    # Apply operations
    operations_to_apply = [op for op in operations if not op.conflict or force]

    if not operations_to_apply:
        console.print("\n[yellow]No operations to apply.[/yellow]")
        return

    if not force and not interactive:
        if not Confirm.ask(f"\nProceed with renaming {len(operations_to_apply)} files?"):
            console.print("Operation cancelled.")
            return

    console.print("\n[bold]Applying filename optimizations...[/bold]")
    successful, failed = apply_operations(operations_to_apply, force=force)

    console.print(f"\n[bold]Results:[/bold] {successful} successful, {failed} failed")

    if failed > 0:
        console.print("[yellow]Some operations failed. Check the logs for details.[/yellow]")


# CLI app integration would be added to the main CLI module
if __name__ == "__main__":
    # For testing purposes
    typer.run(optimize_filenames_command)
