#!/usr/bin/env python3
"""Test script to validate improved filename deduplication logic."""

import sys
sys.path.insert(0, 'src')

from singlefile_archiver.utils.paths import optimize_filename, build_canonical_basename


def test_improved_deduplication():
    """Test cases to validate the improved deduplication logic."""
    print("=== Testing Improved Filename Deduplication Logic ===\n")
    
    # Test case 1: Similar prefixes - should now preserve more distinguishing content
    print("1. Testing similar long prefixes (IMPROVED):")
    similar_titles = [
        "How to Build Modern Web Applications with React and TypeScript",
        "How to Build Modern Web Applications with Vue and JavaScript", 
        "How to Build Modern Web Applications with Angular and TypeScript",
        "How to Build Modern Web Applications with Svelte and TypeScript",
        "How to Build Modern Web Applications with Next.js and TypeScript"
    ]
    
    existing_names = set()
    for title in similar_titles:
        optimized = optimize_filename(title, max_length=50, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 2: News titles with emoji - should preserve more meaningful content
    print("2. Testing news titles with emoji (IMPROVED):")
    news_titles = [
        "🎉 Breaking News: Major Technology Breakthrough Announced Today",
        "🔥 Breaking News: Major Economic Development Reported This Morning", 
        "⚡ Breaking News: Major Political Event Happening Right Now",
        "🚨 Breaking News: Major Environmental Discovery Made Yesterday"
    ]
    
    existing_names = set()
    for title in news_titles:
        optimized = optimize_filename(title, max_length=60, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 3: Progressive truncation with key term preservation
    print("3. Testing progressive truncation with key term preservation (IMPROVED):")
    duplicate_prefixes = [
        "Understanding Machine Learning Algorithms: A Comprehensive Guide for Beginners and Experts",
        "Understanding Machine Learning Algorithms: Advanced Techniques for Data Scientists",
        "Understanding Machine Learning Algorithms: Practical Applications in Real-World Projects"
    ]
    
    existing_names = set()
    for title in duplicate_prefixes:
        optimized = optimize_filename(title, max_length=80, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 4: Technical content with proper nouns
    print("4. Testing technical content with proper nouns (NEW):")
    tech_titles = [
        "Complete Python Programming Tutorial for Data Science Applications",
        "Complete Java Programming Tutorial for Enterprise Applications", 
        "Complete JavaScript Programming Tutorial for Frontend Development",
        "Complete TypeScript Programming Tutorial for Modern Development"
    ]
    
    existing_names = set()
    for title in tech_titles:
        optimized = optimize_filename(title, max_length=55, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())
    
    print("\n" + "="*60 + "\n")
    
    # Test case 5: Canonical basename with improved deduplication
    print("5. Testing canonical basename generation (IMPROVED):")
    test_cases = [
        ("The Ultimate Guide to Python Programming", "https://example.com/python-guide"),
        ("The Ultimate Guide to Java Programming", "https://example.com/java-guide"),
        ("The Ultimate Guide to JavaScript Programming", "https://example.com/js-guide"),
        ("The Ultimate Guide to TypeScript Programming", "https://example.com/ts-guide")
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
    
    print("="*60 + "\n")
    
    # Test case 6: Edge case - very similar titles with subtle differences  
    print("6. Testing edge case - very similar titles (STRESS TEST):")
    edge_titles = [
        "Advanced React Development Patterns and Best Practices for Modern Applications",
        "Advanced React Development Patterns and Best Practices for Enterprise Applications",
        "Advanced React Development Patterns and Best Practices for Scalable Applications",
        "Advanced React Development Patterns and Best Practices for Production Applications"
    ]
    
    existing_names = set()
    for title in edge_titles:
        optimized = optimize_filename(title, max_length=65, existing_names=existing_names)
        print(f"  '{title}' -> '{optimized}'")
        existing_names.add(optimized.lower())


if __name__ == "__main__":
    test_improved_deduplication()