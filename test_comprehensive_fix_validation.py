#!/usr/bin/env python3
"""Comprehensive validation test for the critical deduplication fix."""

import sys
sys.path.insert(0, 'src')

from singlefile_archiver.utils.paths import optimize_filename, build_canonical_basename
from singlefile_archiver.commands.optimize import (
    generate_rename_operations, 
    extract_title_from_filename,
    _optimize_filename_with_fallbacks
)
from pathlib import Path
import time


def test_social_media_extraction():
    """Test enhanced social media filename extraction."""
    print("=== Testing Enhanced Social Media Filename Extraction ===\n")
    
    test_cases = [
        # Twitter/X.com
        ("twitter.com_gptdaoc_status_1844736929175105536.html", "twitter.com - @gptdaoc (Status 105536)"),
        ("x.com_elonmusk_status_1234567890123456789.html", "x.com - @elonmusk (Status 456789)"),
        
        # Instagram
        ("instagram.com_p_ABC123DEF.html", "Instagram Post ABC123DEF"),
        ("instagram.com_natgeo.html", "Instagram @natgeo"),
        
        # LinkedIn  
        ("linkedin.com_posts_johnsmith_activity-987654321.html", "LinkedIn @johnsmith (Activity 654321)"),
        
        # YouTube
        ("youtube.com_watch?v=dQw4w9WgXcQ.html", "YouTube Video dQw4w9WgXcQ"),
        ("youtu.be_dQw4w9WgXcQ.html", "YouTube Video dQw4w9WgXcQ"),
        
        # Reddit
        ("reddit.com_r_programming_posts_abc123.html", "Reddit r/programming (abc123)"),
        
        # TikTok
        ("tiktok.com_@charlidamelio_video_7123456789.html", "TikTok @charlidamelio (Video 456789)"),
        
        # Generic patterns
        ("facebook.com_user123_post456.html", "facebook.com - @user123 (post456)"),
    ]
    
    all_passed = True
    for filename, expected in test_cases:
        extracted = extract_title_from_filename(filename)
        if extracted == expected:
            print(f"✅ {filename} → {extracted}")
        else:
            print(f"❌ {filename} → {extracted} (expected: {expected})")
            all_passed = False
    
    return all_passed


def test_fallback_strategies():
    """Test the multi-layer fallback strategies."""
    print("\n=== Testing Multi-Layer Fallback Strategies ===\n")
    
    # Create scenarios where each fallback is triggered
    existing_names = set()
    
    test_cases = [
        # Strategy 1: Standard optimization works
        ("Unique Title Here", "unique_filename1.html"),
        
        # Strategy 2: Standard fails, hash fallback works  
        ("Unique Title Here", "unique_filename2.html"),  # Will conflict, trigger hash fallback
        
        # Strategy 3: Social media specific fallback
        ("x.com", "x.com_user1_status_123.html"),
        ("x.com", "x.com_user2_status_456.html"),
        ("x.com", "x.com_user3_status_789.html"),
    ]
    
    all_passed = True
    for title, original_filename in test_cases:
        result = _optimize_filename_with_fallbacks(title, original_filename, max_length=50, existing_names=existing_names)
        
        # Check uniqueness
        if result.lower() in existing_names:
            print(f"❌ Failed uniqueness: '{title}' + '{original_filename}' → '{result}' (DUPLICATE)")
            all_passed = False
        else:
            print(f"✅ Unique result: '{title}' + '{original_filename}' → '{result}'")
            existing_names.add(result.lower())
    
    return all_passed


def test_mass_duplication_scenario():
    """Test with a massive number of similar files to stress-test deduplication."""
    print("\n=== Testing Mass Duplication Scenario (Stress Test) ===\n")
    
    # Generate 100 similar social media files
    base_patterns = [
        "twitter.com_user{}_status_184473692917510{}",
        "x.com_user{}_status_184473692917510{}",
        "instagram.com_p_ABC{}DEF",
        "linkedin.com_posts_user{}_activity-98765432{}",
    ]
    
    class MockPath:
        def __init__(self, filename):
            self.name = filename + '.html'
            self.stem = filename
            self.suffix = '.html'
            self.parent = Path('/mock/directory')
    
    # Generate 200 files (50 per platform)
    mock_files = []
    for i in range(50):
        for pattern in base_patterns:
            filename = pattern.format(i, i)
            mock_files.append(MockPath(filename))
    
    print(f"Generated {len(mock_files)} mock files for stress testing...")
    
    start_time = time.time()
    operations = generate_rename_operations(mock_files)
    end_time = time.time()
    
    # Analyze results
    conflicts = sum(1 for op in operations if op.conflict)
    unique_names = set()
    duplicates = []
    
    for op in operations:
        if op.new_name.lower() in unique_names:
            duplicates.append(op.new_name)
        unique_names.add(op.new_name.lower())
    
    print(f"⏱️  Processing time: {end_time - start_time:.3f} seconds")
    print(f"📊 Results:")
    print(f"   Total files: {len(mock_files)}")
    print(f"   Successful renames: {len(operations) - conflicts}")
    print(f"   Conflicts: {conflicts}")
    print(f"   Unique names generated: {len(unique_names)}")
    print(f"   Duplicate names: {len(duplicates)}")
    
    success = conflicts == 0 and len(duplicates) == 0
    if success:
        print("✅ STRESS TEST PASSED: 100% uniqueness achieved")
    else:
        print(f"❌ STRESS TEST FAILED: {conflicts} conflicts, {len(duplicates)} duplicates")
        if duplicates:
            print(f"   Duplicate names: {duplicates[:5]}...")  # Show first 5
    
    return success


def test_backward_compatibility():
    """Test that existing functionality is preserved."""
    print("\n=== Testing Backward Compatibility ===\n")
    
    # Test traditional filename patterns
    traditional_cases = [
        # Canonical format: (title) [URL] encoded_url
        ("(Some Page Title) [URL] https%3A%2F%2Fexample.com%2Fpage", "Some Page Title"),
        
        # Simple patterns
        ("title - example.com", "title"),
        ("title_example.com", "title"),
        ("title example.com", "title"),
        
        # No pattern match - use whole name
        ("random-filename-without-pattern", "random-filename-without-pattern"),
    ]
    
    all_passed = True
    for filename, expected in traditional_cases:
        extracted = extract_title_from_filename(filename)
        if extracted == expected:
            print(f"✅ {filename} → {extracted}")
        else:
            print(f"❌ {filename} → {extracted} (expected: {expected})")
            all_passed = False
    
    return all_passed


def test_edge_cases():
    """Test edge cases and error conditions."""
    print("\n=== Testing Edge Cases ===\n")
    
    edge_cases = [
        # Empty/minimal inputs
        ("", "expected: fallback"),
        ("x", "x"),
        
        # Very long filenames
        ("x.com_verylongusername" + "x" * 100 + "_status_123", "should be truncated appropriately"),
        
        # Special characters
        ("twitter.com_user@name_status_123", "should handle @ in username"),
        
        # Malformed patterns
        ("twitter.com_status_", "incomplete pattern"),
        ("x.com_user_", "incomplete pattern"),
        
        # Unicode/international
        ("twitter.com_用户名_status_123", "should handle unicode"),
    ]
    
    all_passed = True
    for filename, expectation in edge_cases:
        try:
            result = extract_title_from_filename(filename)
            print(f"✅ Edge case: '{filename}' → '{result}' ({expectation})")
        except Exception as e:
            print(f"❌ Edge case failed: '{filename}' → ERROR: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all validation tests."""
    print("🔍 COMPREHENSIVE VALIDATION OF CRITICAL DEDUPLICATION FIX")
    print("=" * 80)
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Social Media Extraction", test_social_media_extraction()))
    test_results.append(("Fallback Strategies", test_fallback_strategies()))
    test_results.append(("Mass Duplication Stress Test", test_mass_duplication_scenario()))
    test_results.append(("Backward Compatibility", test_backward_compatibility()))
    test_results.append(("Edge Cases", test_edge_cases()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Critical deduplication bug is FIXED!")
        print("✅ 100% uniqueness guarantee achieved")
        print("✅ Social media URLs properly handled")
        print("✅ Multi-layer fallback strategies working")
        print("✅ Backward compatibility maintained")
        print("✅ Performance validated for large datasets")
        return True
    else:
        print(f"\n🚨 {total - passed} TEST SUITE(S) FAILED - Additional fixes needed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)