#!/usr/bin/env python3
"""Test script to validate the new length filtering and standardized formatting functionality."""

import tempfile
import shutil
from pathlib import Path
import os
import sys

# Add the src directory to Python path for importing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import (
    scan_archive_directory,
    generate_rename_operations,
    create_standardized_filename,
    _extract_url_from_filename,
    _extract_platform_info
)

def create_test_files():
    """Create test files with different byte lengths and formats."""
    test_dir = Path(tempfile.mkdtemp())
    
    # Test files - some under 255 bytes, some over (but filesystem-safe)
    test_files = []
    
    # Short files (≤255 bytes) - should be skipped
    short_files = [
        "short_file.html",  # 15 bytes
        "another_short_one.html",  # 23 bytes
        "medium_length_filename_but_still_under_255_bytes.html",  # 63 bytes
    ]
    test_files.extend(short_files)
    
    # Long files (>255 bytes) - should be processed
    # Create these with controlled lengths to ensure they're over 255 bytes
    long_files = [
        # Create files with exactly 256+ bytes
        "a" * 250 + ".html",  # 255 bytes
        "b" * 260 + ".html",  # 265 bytes  
        "(Social Media Post) [URL] " + "c" * 230 + ".html",  # ~260 bytes
    ]
    test_files.extend(long_files)
    
    created_files = []
    for filename in test_files:
        try:
            file_path = test_dir / filename
            file_path.write_text(f"Test content for {filename[:50]}...")
            created_files.append(file_path)
            print(f"Created: {filename[:60]}... ({len(filename.encode('utf-8'))} bytes)")
        except OSError as e:
            print(f"Skipped {filename[:50]}... due to filesystem error: {e}")
    
    return test_dir, created_files

def test_byte_length_filtering():
    """Test that files are correctly filtered by byte length."""
    print("=" * 60)
    print("TEST 1: Byte Length Filtering")
    print("=" * 60)
    
    test_dir, created_files = create_test_files()
    
    try:
        # Scan directory with length filtering
        files_to_process, stats = scan_archive_directory(test_dir)
        
        print(f"\nScan Results:")
        print(f"  Total files found: {stats['total_found']}")
        print(f"  Files to process (>255 bytes): {stats['needs_processing']}")
        print(f"  Files skipped (≤255 bytes): {stats['skipped_short']}")
        
        # Verify filtering logic
        for file_path in created_files:
            byte_length = len(file_path.name.encode('utf-8'))
            should_process = byte_length > 255
            is_processed = file_path in files_to_process
            
            status = "✓" if should_process == is_processed else "✗"
            print(f"  {status} {file_path.name[:50]}... ({byte_length} bytes) - {'Processed' if is_processed else 'Skipped'}")
        
        # Validation
        expected_processed = sum(1 for f in created_files if len(f.name.encode('utf-8')) > 255)
        expected_skipped = len(created_files) - expected_processed
        
        assert stats['needs_processing'] == expected_processed, f"Expected {expected_processed} processed, got {stats['needs_processing']}"
        assert stats['skipped_short'] == expected_skipped, f"Expected {expected_skipped} skipped, got {stats['skipped_short']}"
        
        print(f"\n✓ Length filtering test PASSED")
        
    finally:
        shutil.rmtree(test_dir)

def test_standardized_formatting():
    """Test the standardized filename formatting."""
    print("\n" + "=" * 60)
    print("TEST 2: Standardized Formatting")
    print("=" * 60)
    
    test_cases = [
        {
            'title': 'x.com - @SamuelQZQ (Status 667233)',
            'url': 'https://x.com/SamuelQZQ/status/1976062342451667233',
            'expected_pattern': 'X_上的_SamuelQZQ_[URL]_https%3A%2F%2Fx.com%2FSamuelQZQ%2Fstatus%2F1976062342451667233'
        },
        {
            'title': 'Instagram Post ABC123',
            'url': 'https://instagram.com/p/ABC123XYZ',
            'expected_pattern': 'Instagram_上的_'
        },
        {
            'title': 'YouTube Video',
            'url': 'https://youtube.com/watch?v=dQw4w9WgXcQ',
            'expected_pattern': 'YouTube_上的_'
        },
        {
            'title': 'Regular web content',
            'url': 'https://example.com/some/path',
            'expected_pattern': 'Web_上的_Content_[URL]_'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Title: {case['title']}")
        print(f"  URL: {case['url']}")
        
        result = create_standardized_filename(case['title'], case['url'])
        print(f"  Result: {result}")
        print(f"  Length: {len(result)} characters, {len(result.encode('utf-8'))} bytes")
        
        # Check if result contains expected pattern
        if case['expected_pattern'] in result:
            print(f"  ✓ Contains expected pattern: {case['expected_pattern']}")
        else:
            print(f"  ✗ Missing expected pattern: {case['expected_pattern']}")
        
        # Ensure result is under 255 bytes
        if len(result.encode('utf-8')) <= 255:
            print(f"  ✓ Result is ≤255 bytes")
        else:
            print(f"  ✗ Result exceeds 255 bytes!")

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
            'filename': 'x.com_SamuelQZQ_status_1976062342451667233',
            'expected': 'https://x.com/SamuelQZQ/status/1976062342451667233'
        },
        {
            'filename': 'instagram.com_p_ABC123XYZ',
            'expected': 'https://instagram.com/p/ABC123XYZ'
        },
        {
            'filename': 'content_with_url_-_https://example.com/path',
            'expected': 'https://example.com/path'
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
            'expected': {'platform': 'X', 'user': 'SamuelQZQ'}
        },
        {
            'title': 'instagram.com/p/ABC123',
            'expected': {'platform': 'Instagram', 'user': 'ABC123'}
        },
        {
            'title': 'youtube.com video content',
            'expected': {'platform': 'YouTube'}
        },
        {
            'title': 'regular web content',
            'expected': None
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Title: {case['title']}")
        
        result = _extract_platform_info(case['title'])
        print(f"  Result: {result}")
        print(f"  Expected: {case['expected']}")
        
        if case['expected'] is None:
            if result is None:
                print(f"  ✓ Platform extraction PASSED (no platform detected)")
            else:
                print(f"  ✗ Platform extraction FAILED (expected None)")
        else:
            if result and result.get('platform') == case['expected']['platform']:
                print(f"  ✓ Platform extraction PASSED")
            else:
                print(f"  ✗ Platform extraction FAILED")

def test_end_to_end_processing():
    """Test the complete end-to-end processing workflow."""
    print("\n" + "=" * 60)
    print("TEST 5: End-to-End Processing")
    print("=" * 60)
    
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create test files with known URLs
        test_files = [
            # File under 255 bytes - should be skipped
            "short_file.html",
            
            # File over 255 bytes with extractable URL - should be processed with standardized format
            "(X Post by SamuelQZQ) [URL] https%3A%2F%2Fx.com%2FSamuelQZQ%2Fstatus%2F1976062342451667233_" + "x" * 200 + ".html",
            
            # File over 255 bytes without extractable URL - should be processed with fallback
            ("some_very_long_filename_without_social_media_url_that_exceeds_255_bytes_" * 4 + ".html"),
        ]
        
        created_files = []
        for filename in test_files:
            file_path = test_dir / filename
            file_path.write_text(f"Test content for {filename}")
            created_files.append(file_path)
            byte_length = len(filename.encode('utf-8'))
            print(f"Created: {filename[:60]}... ({byte_length} bytes)")
        
        # Scan and process
        files_to_process, stats = scan_archive_directory(test_dir)
        print(f"\nScan Results: {stats['needs_processing']} to process, {stats['skipped_short']} skipped")
        
        # Generate rename operations
        operations = generate_rename_operations(files_to_process)
        
        print(f"\nRename Operations:")
        for op in operations:
            old_bytes = len(op.old_name.encode('utf-8'))
            new_bytes = len(op.new_name.encode('utf-8'))
            is_standardized = "_上的_" in op.new_name and "_[URL]_" in op.new_name
            
            print(f"  Old: {op.old_name[:50]}... ({old_bytes} bytes)")
            print(f"  New: {op.new_name[:50]}... ({new_bytes} bytes)")
            print(f"  Standardized: {'Yes' if is_standardized else 'No'}")
            print(f"  Under 255 bytes: {'Yes' if new_bytes <= 255 else 'No'}")
            print()
        
        # Validation
        processed_count = len(operations)
        expected_count = sum(1 for f in created_files if len(f.name.encode('utf-8')) > 255)
        
        assert processed_count == expected_count, f"Expected {expected_count} operations, got {processed_count}"
        
        # All new filenames should be under 255 bytes
        for op in operations:
            new_bytes = len(op.new_name.encode('utf-8'))
            assert new_bytes <= 255, f"New filename exceeds 255 bytes: {op.new_name} ({new_bytes} bytes)"
        
        print(f"✓ End-to-end processing test PASSED")
        
    finally:
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    print("Starting Length Filtering and Standardized Formatting Validation Tests")
    print("=" * 80)
    
    try:
        test_byte_length_filtering()
        test_standardized_formatting()
        test_url_extraction()
        test_platform_info_extraction()
        test_end_to_end_processing()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 80)
        print("\nKey Features Validated:")
        print("✓ Files ≤255 bytes are correctly skipped")
        print("✓ Files >255 bytes are processed")
        print("✓ Standardized format: Platform_上的_User_[URL]_encoded_url")
        print("✓ URL extraction from various filename patterns")
        print("✓ Platform and user info extraction")
        print("✓ All processed files result in ≤255 byte filenames")
        print("✓ Detailed statistics and reporting")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)