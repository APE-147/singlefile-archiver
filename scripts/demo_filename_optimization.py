#!/usr/bin/env python3
"""
Demo script for filename optimization functionality.
This script demonstrates the filename optimization features without requiring Docker.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from singlefile_archiver.utils.paths import (
    remove_emoji,
    optimize_filename,
    encode_url_for_filename,
    build_canonical_basename,
    safe_filename
)


def demo_emoji_removal():
    """Demonstrate emoji removal functionality."""
    print("🎯 Demo: Emoji Removal")
    print("=" * 50)
    
    test_cases = [
        "Amazing Product Review ⭐️⭐️⭐️⭐️⭐️ Must Read! 🔥",
        "Weather Update: ☀️ Sunny with 🌡️ 25°C", 
        "GitHub: Issue #123 - Fix bug 🐛",
        "Happy Birthday! 🎉🎂🎈",
        "Just text without emoji",
        "Café with naïve résumé",  # Preserve useful Unicode
    ]
    
    for case in test_cases:
        result = remove_emoji(case)
        print(f"Input:  {case}")
        print(f"Output: {result}")
        print()


def demo_filename_optimization():
    """Demonstrate filename length control."""
    print("📏 Demo: Filename Length Control")
    print("=" * 50)
    
    test_cases = [
        ("Short title", 120),
        ("This is an extremely long article title that goes on and on about various topics and eventually becomes too long for practical filesystem use", 80),
        ("Medium length title that needs some truncation", 40),
        ("🎉 Emoji heavy title! ⭐️🔥 With length issues", 50),
    ]
    
    for title, max_length in test_cases:
        result = optimize_filename(title, max_length)
        print(f"Input:  {title}")
        print(f"Limit:  {max_length} chars")
        print(f"Output: {result} ({len(result)} chars)")
        print()


def demo_canonical_basename():
    """Demonstrate canonical basename generation."""
    print("🏗️ Demo: Canonical Basename Generation")
    print("=" * 50)
    
    test_cases = [
        ("Example Page Title", "https://example.com/page"),
        ("Amazing Product Review ⭐️⭐️⭐️⭐️⭐️ Must Read! 🔥", "https://shop.example.com/products/item?id=123&category=electronics"),
        ("Very Long Article Title That Would Normally Cause Issues" * 2, "https://blog.example.com/2024/01/article"),
    ]
    
    for title, url in test_cases:
        result = build_canonical_basename(title, url, max_title_length=60)
        safe_result = safe_filename(result) + ".html"
        print(f"Title: {title}")
        print(f"URL:   {url}")
        print(f"Base:  {result}")
        print(f"Safe:  {safe_result}")
        print()


def demo_feature_flags():
    """Demonstrate feature flag functionality."""
    print("🚩 Demo: Feature Flag Integration")
    print("=" * 50)
    
    # Simulate different feature flag states
    test_scenarios = [
        ("FF_FILENAME_OPTIMIZATION", "false", "Legacy mode"),
        ("FF_FILENAME_OPTIMIZATION", "true", "Optimization enabled"),
        ("FF_BATCH_PROCESSING", "false", "Batch disabled"),
        ("FF_BATCH_PROCESSING", "true", "Batch enabled"),
    ]
    
    for flag, value, description in test_scenarios:
        os.environ[flag] = value
        flag_status = os.getenv(flag, 'false').lower() == 'true'
        print(f"{flag} = {value} → {description} ({'✅' if flag_status else '❌'})")
    
    print()


def demo_complete_workflow():
    """Demonstrate complete filename optimization workflow."""
    print("🔄 Demo: Complete Workflow")
    print("=" * 50)
    
    # Enable optimization
    os.environ['FF_FILENAME_OPTIMIZATION'] = 'true'
    
    # Sample data that might come from a real archiving operation
    sample_url = "https://tech.example.com/articles/2024/advanced-web-scraping-techniques"
    sample_title = "Advanced Web Scraping Techniques 🕷️ Complete Guide 2024 ⭐️⭐️⭐️⭐️⭐️"
    
    print(f"Scenario: Archiving a web page")
    print(f"URL:   {sample_url}")
    print(f"Title: {sample_title}")
    print()
    
    # Step 1: Check feature flag
    use_optimization = os.getenv('FF_FILENAME_OPTIMIZATION', 'false').lower() == 'true'
    print(f"1. Feature flag check: {'✅ Optimization enabled' if use_optimization else '❌ Legacy mode'}")
    
    # Step 2: Generate filename
    if use_optimization:
        basename = build_canonical_basename(sample_title, sample_url, max_title_length=80)
        print(f"2. Canonical basename: {basename}")
    else:
        # Legacy approach (simplified)
        basename = f"({sample_title}) [URL] {sample_url}"
        print(f"2. Legacy basename: {basename}")
    
    # Step 3: Make filesystem safe
    safe_name = safe_filename(basename) + ".html"
    print(f"3. Safe filename: {safe_name}")
    
    # Step 4: Show results
    print(f"4. Final stats:")
    print(f"   - Length: {len(safe_name)} characters")
    print(f"   - Emoji removed: {'Yes' if use_optimization else 'No'}")
    print(f"   - Length controlled: {'Yes' if use_optimization else 'No'}")
    print(f"   - Filesystem safe: Yes")
    print()


def main():
    """Run all demonstrations."""
    print("🚀 SingleFile Archiver - Filename Optimization Demo")
    print("=" * 60)
    print()
    
    demo_emoji_removal()
    demo_filename_optimization()
    demo_canonical_basename()
    demo_feature_flags()
    demo_complete_workflow()
    
    print("✅ Demo Complete!")
    print()
    print("To enable filename optimization in production:")
    print("  export FF_FILENAME_OPTIMIZATION=true")
    print("  export FF_BATCH_PROCESSING=true")
    print()
    print("To use batch processing:")
    print("  python -m singlefile_archiver.commands.optimize /path/to/archives --dry-run")


if __name__ == "__main__":
    main()