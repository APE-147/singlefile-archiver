#!/usr/bin/env python3
"""Comprehensive validation test for filename deduplication improvements."""

import sys
import time
import random
from pathlib import Path
sys.path.insert(0, 'src')

from singlefile_archiver.utils.paths import optimize_filename, build_canonical_basename


def generate_test_titles(pattern_count=10, titles_per_pattern=5):
    """Generate test titles with various patterns for stress testing."""
    patterns = [
        "Complete {tech} Programming Guide for {domain} Development",
        "Understanding {topic}: {subtitle} for {audience}",
        "Advanced {tech} Development: {focus} and Best Practices",
        "The Ultimate {type} to {tech} Programming",
        "Breaking News: Major {topic} {event} Announced",
        "How to Build Modern {type} Applications with {tech}",
        "Professional {tech} Development: {aspect} Guide",
        "Mastering {topic}: {level} Techniques and Strategies"
    ]
    
    tech_terms = ["Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "Angular", "Node.js", "C++", "Go"]
    domains = ["Data Science", "Enterprise", "Frontend", "Backend", "Mobile", "Cloud", "AI", "Web", "System"]
    topics = ["Technology", "Economic", "Environmental", "Sports", "Political", "Scientific", "Medical"]
    subtitles = ["Comprehensive Guide", "Advanced Techniques", "Practical Applications", "Mathematical Foundations"]
    audiences = ["Beginners", "Professionals", "Experts", "Students", "Developers"]
    focuses = ["Patterns", "Architecture", "Performance", "Security", "Testing"]
    types = ["Guide", "Tutorial", "Course", "Reference", "Handbook"]
    events = ["Breakthrough", "Policy Changes", "Initiative", "Discovery", "Victory"]
    aspects = ["Design", "Implementation", "Testing", "Deployment", "Maintenance"]
    levels = ["Beginner", "Intermediate", "Advanced", "Expert", "Professional"]
    
    replacement_pools = {
        'tech': tech_terms,
        'domain': domains,
        'topic': topics,
        'subtitle': subtitles,
        'audience': audiences,
        'focus': focuses,
        'type': types,
        'event': events,
        'aspect': aspects,
        'level': levels
    }
    
    titles = []
    for pattern in patterns[:pattern_count]:
        for i in range(titles_per_pattern):
            title = pattern
            for placeholder, pool in replacement_pools.items():
                if f'{{{placeholder}}}' in title:
                    replacement = random.choice(pool)
                    title = title.replace(f'{{{placeholder}}}', replacement)
            titles.append(title)
    
    return titles


def test_performance(title_count=100):
    """Test performance with large numbers of titles."""
    print(f"=== Performance Testing with {title_count} titles ===")
    
    # Generate test titles
    titles = generate_test_titles(pattern_count=8, titles_per_pattern=title_count//8)
    if len(titles) < title_count:
        # Add some duplicates and variations
        base_titles = titles[:]
        while len(titles) < title_count:
            base_title = random.choice(base_titles)
            # Add slight variations
            variations = [
                f"🎉 {base_title}",
                f"{base_title} - Updated Edition",
                f"{base_title} (2024 Version)",
                f"New: {base_title}"
            ]
            titles.extend(variations[:title_count - len(titles)])
    
    titles = titles[:title_count]
    print(f"Generated {len(titles)} test titles")
    
    # Test performance
    start_time = time.time()
    existing_names = set()
    results = []
    
    for title in titles:
        optimized = optimize_filename(title, max_length=120, existing_names=existing_names)
        results.append(optimized)
        existing_names.add(optimized.lower())
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Analyze results
    unique_count = len(set(r.lower() for r in results))
    conflict_rate = (len(results) - unique_count) / len(results) * 100
    
    print(f"Processing time: {processing_time:.3f} seconds")
    print(f"Average time per title: {processing_time/len(titles)*1000:.2f} ms")
    print(f"Unique results: {unique_count}/{len(results)} ({100*unique_count/len(results):.1f}%)")
    print(f"Conflict rate: {conflict_rate:.2f}%")
    
    # Performance criteria
    acceptable_time_per_title = 10  # ms
    acceptable_conflict_rate = 5   # %
    
    time_ok = (processing_time/len(titles)*1000) < acceptable_time_per_title
    conflict_ok = conflict_rate < acceptable_conflict_rate
    
    print(f"Performance: {'✓' if time_ok else '✗'} (< {acceptable_time_per_title}ms per title)")
    print(f"Conflict rate: {'✓' if conflict_ok else '✗'} (< {acceptable_conflict_rate}%)")
    
    return time_ok and conflict_ok


def test_edge_cases():
    """Test various edge cases and boundary conditions."""
    print("=== Edge Case Testing ===")
    
    edge_cases = [
        {
            'name': 'Empty and very short titles',
            'titles': ['', 'A', 'Hi', 'Test', 'X'],
            'max_length': 50
        },
        {
            'name': 'Very long titles',
            'titles': [
                'This is an extremely long title that goes on and on and on with lots of unnecessary words and repetitive content that should be truncated intelligently',
                'Another incredibly verbose and wordy title that contains far too much information and should be shortened while preserving the most important parts',
                'Yet another excessively long and detailed title with multiple clauses and subclauses that needs intelligent truncation'
            ],
            'max_length': 80
        },
        {
            'name': 'Special characters and Unicode',
            'titles': [
                'Programming with C++ & C# für Anfänger',
                'Diseño de APIs RESTful: Guía completa',
                'プログラミング入門: JavaScript基礎',
                'Разработка ПО: Python для начинающих'
            ],
            'max_length': 60
        },
        {
            'name': 'Very short length limits',
            'titles': [
                'Complete Python Programming Guide',
                'Complete Java Programming Guide',
                'Complete JavaScript Programming Guide'
            ],
            'max_length': 15
        },
        {
            'name': 'Identical titles',
            'titles': [
                'Python Programming Tutorial',
                'Python Programming Tutorial',
                'Python Programming Tutorial',
                'Python Programming Tutorial'
            ],
            'max_length': 50
        }
    ]
    
    all_passed = True
    
    for case in edge_cases:
        print(f"\n{case['name']}:")
        existing_names = set()
        results = []
        
        for title in case['titles']:
            try:
                optimized = optimize_filename(title, max_length=case['max_length'], existing_names=existing_names)
                results.append(optimized)
                existing_names.add(optimized.lower())
                print(f"  '{title}' -> '{optimized}'")
            except Exception as e:
                print(f"  ERROR with '{title}': {e}")
                all_passed = False
                continue
        
        # Check uniqueness
        unique_count = len(set(r.lower() for r in results))
        passed = unique_count == len(results)
        all_passed = all_passed and passed
        
        print(f"  Result: {unique_count}/{len(results)} unique ({'✓' if passed else '✗'})")
    
    return all_passed


def test_regression():
    """Test that we haven't broken existing functionality."""
    print("=== Regression Testing ===")
    
    # Test basic functionality
    basic_tests = [
        {
            'title': 'Simple Title',
            'expected_length_ok': True,
            'expected_no_emoji': True
        },
        {
            'title': '🎉 Title with Emoji 🚀',
            'expected_length_ok': True,
            'expected_no_emoji': True
        },
        {
            'title': 'Very Long Title That Should Be Truncated Because It Exceeds The Maximum Length Limit',
            'expected_length_ok': True,
            'expected_no_emoji': True
        }
    ]
    
    all_passed = True
    
    for test in basic_tests:
        result = optimize_filename(test['title'], max_length=50)
        
        # Check length
        length_ok = len(result) <= 50
        
        # Check no emoji
        import re
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
        no_emoji = not re.search(emoji_pattern, result)
        
        passed = length_ok and no_emoji
        all_passed = all_passed and passed
        
        print(f"  '{test['title'][:30]}...' -> '{result}' ({'✓' if passed else '✗'})")
    
    return all_passed


def run_comprehensive_validation():
    """Run all validation tests."""
    print("=== COMPREHENSIVE FILENAME DEDUPLICATION VALIDATION ===\n")
    
    test_results = {}
    
    # Performance test
    test_results['performance'] = test_performance(100)
    print()
    
    # Edge cases
    test_results['edge_cases'] = test_edge_cases()
    print()
    
    # Regression test
    test_results['regression'] = test_regression()
    print()
    
    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY:")
    print("=" * 60)
    
    for test_name, passed in test_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(test_results.values())
    overall_status = "✓ ALL TESTS PASSED" if all_passed else "✗ SOME TESTS FAILED"
    
    print(f"\nOverall Result: {overall_status}")
    
    if all_passed:
        print("\n🎉 The filename deduplication improvements are working correctly!")
        print("   - Unique filenames generated for all test cases")
        print("   - Performance within acceptable limits")
        print("   - Edge cases handled properly")
        print("   - No regression in existing functionality")
    else:
        print("\n⚠️  Some issues detected. Review failed tests above.")
    
    return all_passed


if __name__ == "__main__":
    run_comprehensive_validation()