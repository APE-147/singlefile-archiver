#!/usr/bin/env python3
"""Test script to validate improved batch processing logic."""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, 'src')

from singlefile_archiver.commands.optimize import generate_rename_operations, extract_title_from_filename, _analyze_title_patterns


def create_test_files(titles_and_content):
    """Create temporary HTML files for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    files = []
    
    for i, (title, content) in enumerate(titles_and_content):
        # Create filename in the format we typically see
        filename = f"({title}) [URL] example.com%2Fpage{i}.html"
        file_path = temp_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><head><title>{title}</title></head><body>{content}</body></html>")
        
        files.append(file_path)
    
    return temp_dir, files


def test_batch_processing_improvements():
    """Test improved batch processing with various scenarios."""
    print("=== Testing Improved Batch Processing Logic ===\n")
    
    # Test scenario 1: Multiple similar programming guides
    print("1. Testing programming guides with similar prefixes:")
    programming_guides = [
        ("🎉 Complete Python Programming Guide for Data Science and Machine Learning", "Python content"),
        ("🔥 Complete Java Programming Guide for Enterprise Development", "Java content"),
        ("⚡ Complete JavaScript Programming Guide for Frontend Development", "JS content"),
        ("🚨 Complete TypeScript Programming Guide for Modern Development", "TS content"),
        ("✨ Complete C++ Programming Guide for System Development", "C++ content")
    ]
    
    temp_dir, files = create_test_files(programming_guides)
    
    try:
        # Extract titles for analysis
        titles = [extract_title_from_filename(f.stem) for f in files]
        print("  Original titles:")
        for title in titles:
            print(f"    - {title}")
        
        # Analyze patterns
        analysis = _analyze_title_patterns(titles)
        print(f"\n  Pattern analysis:")
        print(f"    - Total titles: {analysis.get('total_titles', 0)}")
        print(f"    - Similar groups found: {len(analysis.get('similar_groups', {}))}")
        if analysis.get('similar_groups'):
            for prefix, group_titles in analysis.get('similar_groups', {}).items():
                print(f"      * '{prefix}' group: {len(group_titles)} titles")
        else:
            print("    - No similar groups detected (this might be the issue)")
            print("    - Common prefixes found:")
            for prefix, group_titles in analysis.get('common_prefixes', {}).items():
                if len(group_titles) >= 2:
                    print(f"        '{prefix}': {len(group_titles)} titles")
        
        # Generate operations
        operations = generate_rename_operations(files)
        
        print(f"\n  Generated operations:")
        conflicts = 0
        for op in operations:
            status = "CONFLICT" if op.conflict else "OK"
            if op.conflict:
                conflicts += 1
            print(f"    {status}: '{op.old_name}' -> '{op.new_name}'")
        
        print(f"\n  Summary: {len(operations)} operations, {conflicts} conflicts")
        
    finally:
        # Cleanup
        for file in files:
            file.unlink()
        temp_dir.rmdir()
    
    print("\n" + "="*60 + "\n")
    
    # Test scenario 2: News articles with similar breaking news format
    print("2. Testing news articles with similar formats:")
    news_articles = [
        ("🎉 Breaking News: Major Technology Breakthrough in AI Development Announced", "AI news"),
        ("🔥 Breaking News: Major Economic Policy Changes Impact Global Markets", "Economy news"),
        ("⚡ Breaking News: Major Environmental Initiative Launched by Government", "Environment news"),
        ("🚨 Breaking News: Major Sports Victory Celebrated Across the Nation", "Sports news"),
        ("✨ Breaking News: Major Scientific Discovery Changes Understanding of Physics", "Science news")
    ]
    
    temp_dir, files = create_test_files(news_articles)
    
    try:
        # Extract titles and analyze
        titles = [extract_title_from_filename(f.stem) for f in files]
        analysis = _analyze_title_patterns(titles)
        
        # Generate operations
        operations = generate_rename_operations(files)
        
        print(f"  Pattern analysis: {len(analysis.get('similar_groups', {}))} similar groups found")
        print(f"  Generated {len(operations)} operations:")
        
        conflicts = 0
        for op in operations:
            status = "CONFLICT" if op.conflict else "OK"
            if op.conflict:
                conflicts += 1
            # Show only the new name for brevity
            old_title = extract_title_from_filename(Path(op.old_name).stem)
            new_title = extract_title_from_filename(Path(op.new_name).stem) if not op.conflict else "N/A"
            print(f"    {status}: '{old_title}' -> '{new_title}'")
        
        print(f"\n  Summary: {conflicts} conflicts out of {len(operations)} operations")
        
    finally:
        # Cleanup
        for file in files:
            file.unlink()
        temp_dir.rmdir()
    
    print("\n" + "="*60 + "\n")
    
    # Test scenario 3: Tutorial series with very similar names
    print("3. Testing tutorial series (stress test):")
    tutorial_series = [
        ("Understanding Machine Learning: Comprehensive Guide for Beginners", "ML Basics"),
        ("Understanding Machine Learning: Advanced Techniques for Professionals", "ML Advanced"),
        ("Understanding Machine Learning: Practical Applications in Industry", "ML Practical"),
        ("Understanding Machine Learning: Mathematical Foundations and Theory", "ML Math"),
        ("Understanding Machine Learning: Implementation with Python and TensorFlow", "ML Implementation")
    ]
    
    temp_dir, files = create_test_files(tutorial_series)
    
    try:
        # Extract titles and analyze
        titles = [extract_title_from_filename(f.stem) for f in files]
        analysis = _analyze_title_patterns(titles)
        
        print(f"  Original titles (all start with 'Understanding Machine Learning'):")
        for title in titles:
            unique_part = title.replace("Understanding Machine Learning: ", "")
            print(f"    - ...{unique_part}")
        
        # Generate operations
        operations = generate_rename_operations(files)
        
        print(f"\n  After processing:")
        conflicts = 0
        unique_parts = []
        for op in operations:
            if not op.conflict:
                new_title = extract_title_from_filename(Path(op.new_name).stem)
                unique_parts.append(new_title)
                print(f"    ✓ '{new_title}'")
            else:
                conflicts += 1
                print(f"    ✗ CONFLICT: {op.reason}")
        
        print(f"\n  Uniqueness verification:")
        print(f"    - {len(set(unique_parts))} unique names generated")
        print(f"    - {len(unique_parts) - len(set(unique_parts))} duplicates (should be 0)")
        print(f"    - {conflicts} conflicts")
        
    finally:
        # Cleanup
        for file in files:
            file.unlink()
        temp_dir.rmdir()


if __name__ == "__main__":
    test_batch_processing_improvements()