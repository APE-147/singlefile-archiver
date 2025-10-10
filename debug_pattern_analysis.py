#!/usr/bin/env python3
"""Debug script to understand pattern analysis issues."""

import sys
sys.path.insert(0, 'src')

from singlefile_archiver.commands.optimize import _analyze_title_patterns
from singlefile_archiver.utils.paths import remove_emoji


def debug_pattern_analysis():
    """Debug the pattern analysis logic."""
    print("=== Debugging Pattern Analysis ===\n")
    
    # Test case 1: Original titles with emojis
    print("1. Testing original titles with emojis:")
    original_titles = [
        "🎉 Complete Python Programming Guide for Data Science and Machine Learning",
        "🔥 Complete Java Programming Guide for Enterprise Development",
        "⚡ Complete JavaScript Programming Guide for Frontend Development"
    ]
    
    for title in original_titles:
        print(f"  Original: {title}")
        clean_title = remove_emoji(title)
        print(f"  Clean:    {clean_title}")
        words = clean_title.split()
        print(f"  Words:    {words[:4]}")
        print()
    
    analysis = _analyze_title_patterns(original_titles)
    print(f"Analysis with emojis: {len(analysis.get('similar_groups', {}))} groups")
    if analysis.get('common_prefixes'):
        print("Common prefixes found:")
        for prefix, titles in analysis.get('common_prefixes', {}).items():
            if len(titles) >= 2:
                print(f"  '{prefix}': {len(titles)} titles")
    
    print("\n" + "="*50 + "\n")
    
    # Test case 2: Clean titles without emojis
    print("2. Testing clean titles without emojis:")
    clean_titles = [remove_emoji(title) for title in original_titles]
    
    for title in clean_titles:
        print(f"  Clean: {title}")
        words = title.split()
        print(f"  First 3 words: {' '.join(words[:3])}")
    
    analysis_clean = _analyze_title_patterns(clean_titles)
    print(f"\nAnalysis without emojis: {len(analysis_clean.get('similar_groups', {}))} groups")
    if analysis_clean.get('common_prefixes'):
        print("Common prefixes found:")
        for prefix, titles in analysis_clean.get('common_prefixes', {}).items():
            if len(titles) >= 2:
                print(f"  '{prefix}': {len(titles)} titles")
    
    print("\n" + "="*50 + "\n")
    
    # Test case 3: Breaking news titles
    print("3. Testing breaking news titles:")
    news_titles = [
        "🎉 Breaking News: Major Technology Breakthrough in AI Development Announced",
        "🔥 Breaking News: Major Economic Policy Changes Impact Global Markets",
        "⚡ Breaking News: Major Environmental Initiative Launched by Government"
    ]
    
    clean_news = [remove_emoji(title) for title in news_titles]
    for title in clean_news:
        print(f"  Clean: {title}")
        words = title.split()
        print(f"  First 3 words: {' '.join(words[:3])}")
    
    analysis_news = _analyze_title_patterns(clean_news)
    print(f"\nNews analysis: {len(analysis_news.get('similar_groups', {}))} groups")
    if analysis_news.get('common_prefixes'):
        print("Common prefixes found:")
        for prefix, titles in analysis_news.get('common_prefixes', {}).items():
            if len(titles) >= 2:
                print(f"  '{prefix}': {len(titles)} titles")


if __name__ == "__main__":
    debug_pattern_analysis()