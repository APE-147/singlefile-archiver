#!/usr/bin/env python3
"""Test script to demonstrate current filename duplication issues."""

import sys
sys.path.insert(0, 'src')

from singlefile_archiver.utils.paths import optimize_filename, build_canonical_basename


def test_current_issues():
    """Test cases that demonstrate the current duplication problems."""
    print("=== Testing Current Filename Duplication Issues ===\n")
    
    # Test case 1: Similar prefixes getting truncated the same way
    similar_titles = [
        "How to Build Modern Web Applications with React and TypeScript",
        "How to Build Modern Web Applications with Vue and JavaScript", 
        "How to Build Modern Web Applications with Angular and TypeScript",
        "How to Build Modern Web Applications with Svelte and TypeScript",
        "How to Build Modern Web Applications with Next.js and TypeScript"
    ]
    
    print("1. Testing similar long prefixes:")
    existing_names = set()
    for title in similar_titles:
        optimized = optimize_filename(title, max_length=50, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 2: Short meaningful prefixes getting lost
    news_titles = [
        "🎉 Breaking News: Major Technology Breakthrough Announced Today",
        "🔥 Breaking News: Major Economic Development Reported This Morning", 
        "⚡ Breaking News: Major Political Event Happening Right Now",
        "🚨 Breaking News: Major Environmental Discovery Made Yesterday"
    ]
    
    print("2. Testing news titles with emoji:")
    existing_names = set()
    for title in news_titles:
        optimized = optimize_filename(title, max_length=60, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 3: Current progressive truncation behavior
    duplicate_prefixes = [
        "Understanding Machine Learning Algorithms: A Comprehensive Guide for Beginners and Experts",
        "Understanding Machine Learning Algorithms: Advanced Techniques for Data Scientists",
        "Understanding Machine Learning Algorithms: Practical Applications in Real-World Projects"
    ]
    
    print("3. Testing current progressive truncation:")
    existing_names = set()
    for title in duplicate_prefixes:
        optimized = optimize_filename(title, max_length=80, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 4: Build canonical basename (real-world scenario)
    print("4. Testing canonical basename generation:")
    test_cases = [
        ("The Ultimate Guide to Python Programming", "https://example.com/python-guide"),
        ("The Ultimate Guide to Java Programming", "https://example.com/java-guide"),
        ("The Ultimate Guide to JavaScript Programming", "https://example.com/js-guide")
    ]
    
    existing_names = set()
    for title, url in test_cases:
        basename = build_canonical_basename(title, url, max_title_length=40, existing_names=existing_names)
        print(f"  Title: '{title}'")
        print(f"  URL: '{url}'")
        print(f"  Basename: '{basename}'\n")
        # Extract just the title part for tracking
        title_part = basename.split(') [URL]')[0][1:]  # Remove '(' prefix
        existing_names.add(title_part.lower())


if __name__ == "__main__":
    test_current_issues()