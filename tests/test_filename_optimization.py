"""Tests for filename optimization functionality."""

import pytest
from pathlib import Path

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from singlefile_archiver.utils.paths import (
    remove_emoji,
    optimize_filename,
    encode_url_for_filename,
    build_canonical_basename,
    safe_filename
)


class TestRemoveEmoji:
    """Test emoji removal functionality."""
    
    def test_remove_common_emoji(self):
        """Test removal of common emoji characters."""
        test_cases = [
            ("Amazing Product Review ⭐️⭐️⭐️⭐️⭐️ Must Read! 🔥", "Amazing Product Review Must Read!"),
            ("Weather Update: ☀️ Sunny with 🌡️ 25°C", "Weather Update: Sunny with 25°C"),
            ("GitHub: Issue #123 - Fix bug 🐛", "GitHub: Issue #123 - Fix bug"),
            ("Happy Birthday! 🎉🎂🎈", "Happy Birthday!"),
            ("Just text without emoji", "Just text without emoji"),
            ("", ""),
        ]
        
        for input_text, expected in test_cases:
            result = remove_emoji(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_preserve_unicode_characters(self):
        """Test that non-emoji Unicode characters are preserved."""
        test_cases = [
            ("Café with naïve résumé", "Café with naïve résumé"),
            ("日本語のテスト", "日本語のテスト"),
            ("Москва", "Москва"),
            ("25°C temperature", "25°C temperature"),
        ]
        
        for input_text, expected in test_cases:
            result = remove_emoji(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_whitespace_cleanup(self):
        """Test that extra whitespace is cleaned up."""
        test_cases = [
            ("Text   with    extra     spaces", "Text with extra spaces"),
            ("  Leading and trailing  ", "Leading and trailing"),
            ("🎉   Multiple   🎂   emoji   🎈", "Multiple emoji"),
        ]
        
        for input_text, expected in test_cases:
            result = remove_emoji(input_text)
            assert result == expected, f"Failed for input: {input_text}"


class TestOptimizeFilename:
    """Test filename optimization functionality."""
    
    def test_short_filenames_unchanged(self):
        """Test that short filenames remain unchanged."""
        short_titles = [
            "Short title",
            "GitHub Issue",
            "Product Review",
        ]
        
        for title in short_titles:
            result = optimize_filename(title, max_length=120)
            assert result == title
    
    def test_long_filename_truncation(self):
        """Test truncation of long filenames."""
        long_title = "This is an extremely long article title that goes on and on about various topics and eventually becomes too long for practical filesystem use and needs to be truncated"
        
        result = optimize_filename(long_title, max_length=50)
        
        assert len(result) <= 50
        assert result.endswith("...")
        assert "This is an extremely long article title" in result
    
    def test_word_boundary_truncation(self):
        """Test that truncation prefers word boundaries."""
        title = "A reasonably long title that should be truncated at word boundaries"
        
        result = optimize_filename(title, max_length=30)
        
        assert len(result) <= 30
        assert result.endswith("...")
        # Should break at a word boundary, not in the middle of a word
        assert not result[:-3].endswith(("reasonab", "truncat"))
    
    def test_emoji_removal_in_optimization(self):
        """Test that emoji are removed during optimization."""
        title_with_emoji = "Amazing Product Review ⭐️⭐️⭐️⭐️⭐️ Must Read! 🔥"
        
        result = optimize_filename(title_with_emoji)
        
        assert "⭐️" not in result
        assert "🔥" not in result
        assert "Amazing Product Review Must Read!" == result
    
    def test_empty_title_fallback(self):
        """Test fallback for empty or emoji-only titles."""
        test_cases = [
            "",
            "🎉🎂🎈",
            "   ",
            None,
        ]
        
        for title in test_cases:
            result = optimize_filename(title or "")
            assert result == "untitled"


class TestEncodeUrlForFilename:
    """Test URL encoding for filenames."""
    
    def test_basic_url_encoding(self):
        """Test basic URL encoding."""
        url = "https://example.com/page?param=value"
        result = encode_url_for_filename(url)
        
        assert "%3A" in result  # Encoded colon
        assert "%3F" in result  # Encoded question mark
        assert "example.com" in result
    
    def test_url_length_limit(self):
        """Test URL length limiting."""
        long_url = "https://example.com/" + "very-long-path/" * 20 + "page.html"
        
        result = encode_url_for_filename(long_url, max_length=50)
        
        assert len(result) <= 50
        assert result.endswith("...")
    
    def test_empty_url_fallback(self):
        """Test fallback for empty URLs."""
        result = encode_url_for_filename("")
        assert result == "no-url"


class TestBuildCanonicalBasename:
    """Test canonical basename building."""
    
    def test_canonical_format(self):
        """Test the canonical format structure."""
        title = "Example Page Title"
        url = "https://example.com/page"
        
        result = build_canonical_basename(title, url)
        
        assert result.startswith("(Example Page Title)")
        assert "[URL]" in result
        assert "example.com" in result
    
    def test_long_title_optimization(self):
        """Test that long titles are optimized in canonical format."""
        long_title = "This is an extremely long title that should be truncated" * 3
        url = "https://example.com/page"
        
        result = build_canonical_basename(long_title, url, max_title_length=50)
        
        # The title portion should be truncated
        title_part = result.split(")")[0][1:]  # Extract title from (title)
        assert len(title_part) <= 50
        assert title_part.endswith("...")
    
    def test_emoji_removal_in_canonical(self):
        """Test emoji removal in canonical basename."""
        title = "Great Article! 🎉⭐️"
        url = "https://example.com/article"
        
        result = build_canonical_basename(title, url)
        
        assert "🎉" not in result
        assert "⭐️" not in result
        assert "Great Article!" in result


class TestSafeFilename:
    """Test safe filename generation."""
    
    def test_unsafe_character_replacement(self):
        """Test replacement of unsafe characters."""
        unsafe_filename = 'file<with>unsafe:chars"/\\|?*'
        
        result = safe_filename(unsafe_filename)
        
        for char in '<>:"/\\|?*':
            assert char not in result
        assert "_" in result  # Unsafe chars replaced with underscores
    
    def test_length_limiting_with_hash(self):
        """Test length limiting with stable hash."""
        long_filename = "a" * 300
        
        result = safe_filename(long_filename, max_length=100)
        
        assert len(result) <= 100
        assert "_" in result and result.split("_")[-1].isdigit()  # Should have hash suffix
    
    def test_empty_filename_fallback(self):
        """Test fallback for empty filenames."""
        result = safe_filename("")
        assert result == "untitled"
    
    def test_stable_hash_consistency(self):
        """Test that the same input produces the same hash."""
        filename = "test filename for hash consistency"
        
        result1 = safe_filename(filename, max_length=10)
        result2 = safe_filename(filename, max_length=10)
        
        assert result1 == result2  # Should be consistent


class TestIntegration:
    """Integration tests for the complete filename optimization pipeline."""
    
    def test_complete_optimization_pipeline(self):
        """Test the complete optimization from title to final filename."""
        title = "Amazing Product Review ⭐️⭐️⭐️⭐️⭐️ Must Read! 🔥 " * 3
        url = "https://example.com/reviews/product?id=123&category=electronics"
        
        # Build canonical basename
        basename = build_canonical_basename(title, url, max_title_length=80)
        
        # Make it filesystem safe
        safe_name = safe_filename(basename)
        
        # Verify the result
        assert len(safe_name) <= 255  # Filesystem limit
        assert "⭐️" not in safe_name
        assert "🔥" not in safe_name
        assert "Amazing Product Review Must Read!" in safe_name
        assert "example.com" in safe_name
        
    def test_conflict_resolution_simulation(self):
        """Test how filenames would be handled with conflicts."""
        base_title = "Duplicate Article Title"
        url = "https://example.com/article"
        
        # Generate multiple filenames that would conflict
        names = []
        for i in range(5):
            if i == 0:
                title = base_title
            else:
                title = f"{base_title} 2024010{i}_120000"  # Simulate timestamp
            
            basename = build_canonical_basename(title, url)
            safe_name = safe_filename(basename) + ".html"
            names.append(safe_name)
        
        # Verify all names are different
        assert len(set(names)) == len(names), "All generated names should be unique"


if __name__ == "__main__":
    pytest.main([__file__])