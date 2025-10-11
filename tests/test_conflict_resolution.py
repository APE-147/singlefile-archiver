#!/usr/bin/env python3
"""Test script to validate enhanced conflict resolution in batch filename optimization."""

import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from singlefile_archiver.commands.optimize import (
    _ensure_unique_filename,
    generate_rename_operations,
    extract_title_from_filename,
    create_standardized_filename,
    create_enhanced_content_filename
)


def test_ensure_unique_filename():
    """Test the enhanced _ensure_unique_filename function."""
    print("=== Testing _ensure_unique_filename ===")
    
    # Test case 1: No existing conflicts
    result = _ensure_unique_filename("X_上的_宝玉_测试内容", set(), max_bytes=150)
    assert result == "X_上的_宝玉_测试内容"
    print("✓ No conflict case works")
    
    # Test case 2: Basic conflict resolution
    existing = {"x_上的_宝玉_测试内容"}
    result = _ensure_unique_filename("X_上的_宝玉_测试内容", existing, max_bytes=150)
    assert result == "X_上的_宝玉_测试内容_001"
    print("✓ Basic conflict resolution works")
    
    # Test case 3: Multiple conflicts
    existing = {
        "x_上的_宝玉_测试内容", 
        "x_上的_宝玉_测试内容_001",
        "x_上的_宝玉_测试内容_002"
    }
    result = _ensure_unique_filename("X_上的_宝玉_测试内容", existing, max_bytes=150)
    assert result == "X_上的_宝玉_测试内容_003"
    print("✓ Multiple conflict resolution works")
    
    # Test case 4: Byte length constraint with truncation
    long_name = "X_上的_很长的用户名_这是一个非常非常长的内容描述用来测试字节长度限制功能是否正常工作"
    existing = {long_name.lower()}
    result = _ensure_unique_filename(long_name, existing, max_bytes=150)
    
    # Verify the result fits within byte constraints
    result_bytes = len((result + ".html").encode('utf-8'))
    assert result_bytes <= 150, f"Result {result_bytes} bytes exceeds 150 byte limit"
    assert result.endswith("_001"), f"Expected _001 suffix, got: {result}"
    print(f"✓ Byte constraint with truncation works: {result_bytes} bytes")
    
    # Test case 5: Extreme truncation
    very_long = "X_上的_" + "非常长的用户名" * 10 + "_" + "超级长的内容" * 20
    existing = {very_long.lower()}
    result = _ensure_unique_filename(very_long, existing, max_bytes=100)  # Tight constraint
    
    result_bytes = len((result + ".html").encode('utf-8'))
    assert result_bytes <= 100, f"Result {result_bytes} bytes exceeds 100 byte limit"
    print(f"✓ Extreme truncation works: {result_bytes} bytes")


def test_create_conflict_scenario():
    """Create a realistic conflict scenario and test resolution."""
    print("\n=== Testing Realistic Conflict Scenario ===")
    
    # Create test filenames that would conflict
    test_titles = [
        "X_上的_宝玉_OpenAI新功能分析",
        "X_上的_宝玉_OpenAI新功能分析",  # Exact duplicate
        "X_上的_宝玉_OpenAI新功能分析",  # Another duplicate
        "X_上的_宝玉_OpenAI新功能详解",  # Similar but different
        "X_上的_宝玉_OpenAI新功能详解",  # Duplicate of the above
    ]
    
    existing_names = set()
    unique_results = []
    
    for title in test_titles:
        unique_name = _ensure_unique_filename(title, existing_names, max_bytes=150)
        existing_names.add(unique_name.lower())
        unique_results.append(unique_name)
        print(f"  {title} → {unique_name}")
    
    # Verify all results are unique
    assert len(set(r.lower() for r in unique_results)) == len(unique_results), "Results are not unique!"
    
    # Verify expected pattern
    assert unique_results[0] == "X_上的_宝玉_OpenAI新功能分析"
    assert unique_results[1] == "X_上的_宝玉_OpenAI新功能分析_001"
    assert unique_results[2] == "X_上的_宝玉_OpenAI新功能分析_002"
    assert unique_results[3] == "X_上的_宝玉_OpenAI新功能详解"
    assert unique_results[4] == "X_上的_宝玉_OpenAI新功能详解_001"
    
    print("✓ All results are unique with correct numbering pattern")


def test_batch_processing_integration():
    """Test the full batch processing with conflict resolution."""
    print("\n=== Testing Batch Processing Integration ===")
    
    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files that would generate conflicts
        test_files = [
            "X_上的_宝玉_OpenAI技术分析_这是一个很长的描述来测试重复情况的处理_额外内容让文件名超过255字节的限制.html",
            "X_上的_宝玉_OpenAI技术分析_这是一个很长的描述来测试重复情况的处理_额外内容让文件名超过255字节的限制_v2.html",
            "X_上的_宝玉_OpenAI技术分析_这是一个很长的描述来测试重复情况的处理_额外内容让文件名超过255字节的限制_final.html",
        ]
        
        file_paths = []
        for filename in test_files:
            file_path = temp_path / filename
            file_path.write_text("test content")
            file_paths.append(file_path)
        
        # Generate rename operations
        operations = generate_rename_operations(file_paths)
        
        print(f"Generated {len(operations)} operations:")
        
        new_names = []
        for op in operations:
            print(f"  {op.old_name}")
            print(f"  → {op.new_name}")
            print(f"  Conflict: {op.conflict}")
            print(f"  Bytes: {len(op.old_name.encode('utf-8'))} → {len(op.new_name.encode('utf-8'))}")
            print()
            
            # Verify new name fits constraints
            assert len(op.new_name.encode('utf-8')) <= 255, f"New name exceeds 255 bytes: {op.new_name}"
            
            new_names.append(op.new_name.lower())
        
        # Verify all new names are unique
        assert len(set(new_names)) == len(new_names), f"Generated names are not unique: {new_names}"
        print("✓ All generated names are unique and within byte constraints")


def test_edge_cases():
    """Test edge cases for conflict resolution."""
    print("\n=== Testing Edge Cases ===")
    
    # Test case 1: Very short base name
    short_name = "短"
    existing = {"短"}
    result = _ensure_unique_filename(short_name, existing, max_bytes=50)
    assert result == "短_001"
    print("✓ Very short name handled correctly")
    
    # Test case 2: Name with special characters
    special_name = "X_上的_user-name_content:test"
    existing = {"x_上的_user-name_content:test"}
    result = _ensure_unique_filename(special_name, existing, max_bytes=150)
    assert result == "X_上的_user-name_content:test_001"
    print("✓ Special characters handled correctly")
    
    # Test case 3: Maximum conflicts (999)
    base_name = "test"
    existing = {f"test_{i:03d}" for i in range(1, 999)}
    existing.add("test")
    result = _ensure_unique_filename(base_name, existing, max_bytes=50)
    assert result == "test_999"
    print("✓ Maximum conflict number handled correctly")
    
    # Test case 4: Timestamp fallback when all numbers are taken
    base_name = "test"
    existing = {f"test_{i:03d}" for i in range(1, 1000)}  # All numbers taken
    existing.add("test")
    result = _ensure_unique_filename(base_name, existing, max_bytes=50)
    assert result.startswith("test_") and len(result.split("_")[-1]) == 6  # timestamp format
    print("✓ Timestamp fallback works when all numbers taken")


def test_real_world_examples():
    """Test with real-world examples that users reported."""
    print("\n=== Testing Real-World Examples ===")
    
    # Example from user requirements
    examples = [
        "X_上的_宝玉_OpenAI新功能分析.html",
        "X_上的_宝玉_OpenAI新功能分析.html",  # Conflict!
    ]
    
    # Simulate what would happen in batch processing
    existing_names = set()
    results = []
    
    for example in examples:
        stem = Path(example).stem
        unique_stem = _ensure_unique_filename(stem, existing_names, max_bytes=150)
        existing_names.add(unique_stem.lower())
        final_name = unique_stem + ".html"
        results.append(final_name)
        print(f"  {example} → {final_name}")
    
    # Verify the expected outcome from user requirements
    assert results[0] == "X_上的_宝玉_OpenAI新功能分析.html"
    assert results[1] == "X_上的_宝玉_OpenAI新功能分析_001.html"
    
    print("✓ Real-world example matches user requirements exactly")


def main():
    """Run all tests."""
    print("Testing Enhanced Conflict Resolution for Batch Filename Optimization")
    print("=" * 70)
    
    try:
        test_ensure_unique_filename()
        test_create_conflict_scenario()
        test_batch_processing_integration()
        test_edge_cases()
        test_real_world_examples()
        
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("✓ Conflict detection works correctly")
        print("✓ Numbered suffixes (_001, _002, _003) are properly added")
        print("✓ Byte length constraints are respected")
        print("✓ 100% unique filenames are guaranteed")
        print("✓ Integration with batch processing works")
        print("✓ Real-world examples produce expected results")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)