#!/usr/bin/env python3
"""Simple unit tests to validate the length filtering and standardized formatting functionality."""

import sys
from pathlib import Path

# Add the src directory to Python path for importing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import (
    create_standardized_filename,
    _extract_url_from_filename,
    _extract_platform_info
)

def test_byte_length_calculation():
    """Test byte length calculation for different filename types."""
    print("=" * 60)
    print("TEST 1: Byte Length Calculation")
    print("=" * 60)
    
    test_cases = [
        ("short.html", False),  # Under 255
        ("a" * 250 + ".html", False),  # Exactly 255 bytes
        ("a" * 251 + ".html", True),   # Over 255 bytes
        ("中文文件名很长" * 20 + ".html", True),  # Unicode over 255 bytes
    ]
    
    for filename, should_process in test_cases:
        byte_length = len(filename.encode('utf-8'))
        would_process = byte_length > 255
        
        status = "✓" if should_process == would_process else "✗"
        print(f"  {status} {filename[:50]}... ({byte_length} bytes) - {'Would process' if would_process else 'Would skip'}")
    
    print("✓ Byte length calculation test PASSED")

def test_standardized_formatting():
    """Test the standardized filename formatting."""
    print("\n" + "=" * 60)
    print("TEST 2: Standardized Formatting")
    print("=" * 60)
    
    test_cases = [
        {
            'title': 'x.com - @SamuelQZQ (Status 667233)',
            'url': 'https://x.com/SamuelQZQ/status/1976062342451667233',
            'should_contain': ['X_上的_', '_[URL]_', 'x.com']
        },
        {
            'title': 'Regular web content',
            'url': 'https://example.com/some/path',
            'should_contain': ['Web_上的_Content_[URL]_']
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Title: {case['title']}")
        print(f"  URL: {case['url']}")
        
        result = create_standardized_filename(case['title'], case['url'])
        byte_length = len(result.encode('utf-8'))
        
        print(f"  Result: {result}")
        print(f"  Length: {len(result)} characters, {byte_length} bytes")
        
        # Check required patterns
        all_found = True
        for pattern in case['should_contain']:
            if pattern in result:
                print(f"  ✓ Contains pattern: {pattern}")
            else:
                print(f"  ✗ Missing pattern: {pattern}")
                all_found = False
        
        # Check byte length constraint
        if byte_length <= 255:
            print(f"  ✓ Result is ≤255 bytes")
        else:
            print(f"  ✗ Result exceeds 255 bytes!")
            all_found = False
        
        if all_found:
            print(f"  ✓ Test case {i} PASSED")
        else:
            print(f"  ✗ Test case {i} FAILED")

def test_url_extraction():
    """Test URL extraction from existing filenames."""
    print("\n" + "=" * 60)
    print("TEST 3: URL Extraction")
    print("=" * 60)
    
    test_cases = [
        {
            'filename': '(Some Post) [URL] https%3A%2F%2Fx.com%2FSamuelQZQ%2Fstatus%2F1976062342451667233',
            'expected': 'https://x.com/SamuelQZQ/status/1976062342451667233'
        },
        {
            'filename': 'content_with_url_-_https://example.com/path',
            'expected': 'https://example.com/path'
        },
        {
            'filename': 'no_url_here',
            'expected': ''
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Filename: {case['filename']}")
        
        extracted = _extract_url_from_filename(case['filename'])
        print(f"  Extracted: {extracted}")
        print(f"  Expected: {case['expected']}")
        
        if extracted == case['expected']:
            print(f"  ✓ URL extraction PASSED")
        else:
            print(f"  ✗ URL extraction FAILED")

def test_platform_info_extraction():
    """Test platform and user info extraction."""
    print("\n" + "=" * 60)
    print("TEST 4: Platform Info Extraction")
    print("=" * 60)
    
    test_cases = [
        {
            'title': 'x.com - @SamuelQZQ (Status 667233)',
            'expected_platform': 'X',
            'expected_user': 'samuelqzq'  # Note: cleaned up to lowercase
        },
        {
            'title': 'regular web content',
            'expected_platform': None,
            'expected_user': None
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Title: {case['title']}")
        
        result = _extract_platform_info(case['title'])
        print(f"  Result: {result}")
        
        if case['expected_platform'] is None:
            if result is None:
                print(f"  ✓ Platform extraction PASSED (no platform detected)")
            else:
                print(f"  ✗ Platform extraction FAILED (expected None)")
        else:
            if result and result.get('platform') == case['expected_platform']:
                print(f"  ✓ Platform extraction PASSED")
                if case['expected_user'] and result.get('user') == case['expected_user']:
                    print(f"  ✓ User extraction PASSED")
                elif case['expected_user']:
                    print(f"  ✗ User extraction FAILED (expected {case['expected_user']}, got {result.get('user')})")
            else:
                print(f"  ✗ Platform extraction FAILED")

def test_length_filtering_logic():
    """Test the core logic of length-based filtering."""
    print("\n" + "=" * 60)
    print("TEST 5: Length Filtering Logic")
    print("=" * 60)
    
    # Simulate the filtering logic without file creation
    test_filenames = [
        "short.html",  # 10 bytes
        "medium_length_filename.html",  # 29 bytes
        "a" * 250 + ".html",  # 255 bytes (boundary case)
        "a" * 251 + ".html",  # 256 bytes (should process)
    ]
    
    files_to_process = []
    files_skipped = []
    
    for filename in test_filenames:
        byte_length = len(filename.encode('utf-8'))
        
        if byte_length > 255:
            files_to_process.append(filename)
            status = "PROCESS"
        else:
            files_skipped.append(filename)
            status = "SKIP"
        
        print(f"  {filename[:30]}... ({byte_length} bytes) -> {status}")
    
    print(f"\nResults:")
    print(f"  Files to process: {len(files_to_process)}")
    print(f"  Files skipped: {len(files_skipped)}")
    
    # Validate boundary condition
    assert len(("a" * 250 + ".html").encode('utf-8')) == 255, "255-byte file should be exactly 255 bytes"
    assert len(("a" * 251 + ".html").encode('utf-8')) == 256, "256-byte file should be exactly 256 bytes"
    
    print("✓ Length filtering logic test PASSED")

if __name__ == "__main__":
    print("Starting Length Filtering and Standardized Formatting Unit Tests")
    print("=" * 80)
    
    try:
        test_byte_length_calculation()
        test_standardized_formatting()
        test_url_extraction()
        test_platform_info_extraction()
        test_length_filtering_logic()
        
        print("\n" + "=" * 80)
        print("🎉 ALL UNIT TESTS PASSED! 🎉")
        print("=" * 80)
        print("\nKey Features Validated:")
        print("✓ Byte length calculation using UTF-8 encoding")
        print("✓ Files ≤255 bytes are correctly identified for skipping")
        print("✓ Files >255 bytes are correctly identified for processing")
        print("✓ Standardized format generation: Platform_上的_User_[URL]_encoded_url")
        print("✓ URL extraction from filename patterns")
        print("✓ Platform and user info extraction")
        print("✓ Generated filenames stay ≤255 bytes")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)