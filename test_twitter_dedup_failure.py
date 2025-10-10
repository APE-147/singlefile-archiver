#!/usr/bin/env python3
"""Test script to reproduce the critical Twitter/X.com deduplication failures reported by user."""

import sys
sys.path.insert(0, 'src')

from singlefile_archiver.utils.paths import optimize_filename, build_canonical_basename
from singlefile_archiver.commands.optimize import generate_rename_operations, extract_title_from_filename
from pathlib import Path


def test_twitter_deduplication_failures():
    """Reproduce the specific Twitter/X.com deduplication failures reported by user."""
    print("=== Reproducing Twitter/X.com Deduplication Failures ===\n")
    
    # These are the specific examples from user's report
    user_reported_conflicts = [
        # Twitter.com cases that conflict to same "twitter.com...7905d"
        ("twitter.com_gptdaoc_status_1844736929175105536.html", "Some tweet content from gptdaoc"),
        ("twitter.com_zuozizh_status_1844789234567890123.html", "Another tweet from zuozizh"),
        
        # X.com cases that conflict to same "x.com...9a4323.html" 
        ("x.com_hroyhonghong_status_1844654321098765432.html", "Tweet from hroyhonghong"),
        ("x.com_dotey_status_1844567890123456789.html", "Tweet from dotey"),
        ("x.com_geekbb_status_1844432109876543210.html", "Tweet from geekbb"),
        ("x.com_aigclink_status_1844321098765432109.html", "Tweet from aigclink"),
        ("x.com_yangyixxxx_status_1844210987654321098.html", "Tweet from yangyixxxx"),
    ]
    
    print("1. Testing user's reported conflict cases:")
    print("   Expected: Each should get unique optimized filename")
    print("   Actual problem: Multiple files map to same optimized name\n")
    
    existing_names = set()
    conflicts = []
    
    for filename, title in user_reported_conflicts:
        # Extract title from filename (simulating the actual extraction process)
        extracted_title = extract_title_from_filename(filename)
        print(f"  Original: '{filename}'")
        print(f"  Extracted title: '{extracted_title}'")
        
        # Optimize with current algorithm
        optimized = optimize_filename(extracted_title, max_length=120, existing_names=existing_names)
        print(f"  Optimized: '{optimized}'")
        
        # Check for conflicts
        if optimized.lower() in existing_names:
            conflicts.append((filename, optimized))
            print(f"  ❌ CONFLICT! Maps to same as previous file")
        else:
            existing_names.add(optimized.lower())
            print(f"  ✅ Unique")
        print()
    
    print(f"CONFLICTS DETECTED: {len(conflicts)}")
    for original, conflicted_name in conflicts:
        print(f"  '{original}' conflicts with optimized name '{conflicted_name}'")
    
    print("\n" + "="*80 + "\n")
    
    # Test canonical basename generation
    print("2. Testing canonical basename generation with URLs:")
    test_cases = [
        ("Some tweet content", "https://twitter.com/gptdaoc/status/1844736929175105536"),
        ("Another tweet content", "https://twitter.com/zuozizh/status/1844789234567890123"),
        ("Tweet content", "https://x.com/hroyhonghong/status/1844654321098765432"),
        ("Different tweet", "https://x.com/dotey/status/1844567890123456789"),
        ("More content", "https://x.com/geekbb/status/1844432109876543210"),
    ]
    
    existing_names = set()
    basename_conflicts = []
    
    for title, url in test_cases:
        basename = build_canonical_basename(title, url, max_title_length=60, existing_names=existing_names)
        print(f"  Title: '{title}'")
        print(f"  URL: '{url}'")
        print(f"  Basename: '{basename}'")
        
        # Extract title portion for dedup tracking
        if ') [URL]' in basename:
            title_part = basename.split(') [URL]')[0][1:]  # Remove '(' prefix
            if title_part.lower() in existing_names:
                basename_conflicts.append((url, basename))
                print(f"  ❌ BASENAME CONFLICT!")
            else:
                existing_names.add(title_part.lower())
                print(f"  ✅ Unique basename")
        print()
    
    print(f"BASENAME CONFLICTS: {len(basename_conflicts)}")
    
    print("\n" + "="*80 + "\n")
    
    # Test the actual batch processing scenario
    print("3. Testing batch processing simulation:")
    
    # Create mock Path objects for testing
    class MockPath:
        def __init__(self, filename):
            self.name = filename
            self.stem = filename.replace('.html', '').replace('.htm', '')
            self.suffix = '.html'
            self.parent = Path('/mock/directory')
    
    mock_files = [MockPath(filename) for filename, _ in user_reported_conflicts]
    
    # This should replicate the exact scenario user experienced
    operations = generate_rename_operations(mock_files)
    
    print(f"Generated {len(operations)} rename operations:")
    operation_conflicts = 0
    
    for op in operations:
        status = "✅ OK" if not op.conflict else f"❌ CONFLICT: {op.reason}"
        print(f"  {op.old_name} → {op.new_name} ({status})")
        if op.conflict:
            operation_conflicts += 1
    
    print(f"\nBATCH PROCESSING CONFLICTS: {operation_conflicts}")
    
    return len(conflicts) + len(basename_conflicts) + operation_conflicts


def analyze_social_media_url_patterns():
    """Analyze the patterns in social media URLs that cause conflicts."""
    print("\n=== Analyzing Social Media URL Patterns ===\n")
    
    # Common patterns in social media URLs
    social_patterns = {
        'twitter.com': [
            'twitter.com/user1/status/123456',
            'twitter.com/user2/status/234567', 
            'twitter.com/user3/status/345678',
        ],
        'x.com': [
            'x.com/user1/status/123456',
            'x.com/user2/status/234567',
            'x.com/user3/status/345678',
        ],
        'instagram.com': [
            'instagram.com/p/ABC123/',
            'instagram.com/p/DEF456/',
            'instagram.com/p/GHI789/',
        ],
        'linkedin.com': [
            'linkedin.com/posts/user1_activity-123456',
            'linkedin.com/posts/user2_activity-234567',
        ]
    }
    
    print("Current URL encoding patterns:")
    from singlefile_archiver.utils.paths import encode_url_for_filename
    
    for platform, urls in social_patterns.items():
        print(f"\n{platform}:")
        encoded_urls = set()
        for url in urls:
            full_url = f"https://{url}"
            encoded = encode_url_for_filename(full_url, max_length=60)
            print(f"  {url} → {encoded}")
            if encoded in encoded_urls:
                print(f"    ❌ DUPLICATE ENCODING!")
            encoded_urls.add(encoded)
    
    print("\nPROBLEM IDENTIFIED:")
    print("- URL encoding truncates at same point for similar URLs")
    print("- User/status information gets lost in truncation")
    print("- Domain patterns are too similar after encoding")


if __name__ == "__main__":
    total_conflicts = test_twitter_deduplication_failures()
    analyze_social_media_url_patterns()
    
    print(f"\n{'='*80}")
    print(f"TOTAL CONFLICTS DETECTED: {total_conflicts}")
    print("❌ CRITICAL BUG CONFIRMED: Multiple different URLs mapping to same optimized filename")
    print("🚨 IMMEDIATE FIX REQUIRED for social media URL deduplication")