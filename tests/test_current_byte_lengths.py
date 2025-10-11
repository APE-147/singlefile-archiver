#!/usr/bin/env python3
"""Test current byte lengths to understand the problem."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import create_enhanced_content_filename, create_standardized_filename

def test_current_lengths():
    """Test current byte lengths with the existing implementation."""
    
    # User's test cases - these are examples from their feedback
    test_cases = [
        {
            'description': 'Case 1: X_上的_宝玉 - OpenAI content',
            'title': 'X_上的_宝玉_OpenAI新的产品ChatGPT功能详细解析和使用指南',
            'url': 'https://x.com/baozhu/status/123456'
        },
        {
            'description': 'Case 2: X_上的_宝玉 - LONGER content',
            'title': 'X_上的_宝玉_比特币总裁：过去数年我一直在思考如何让更多人了解和接受加密货币技术的重要性',
            'url': None  # No URL - should use enhanced content format
        },
        {
            'description': 'Case 3: X_上的_DN-Samuel - very long',
            'title': 'X_上的_DN-Samuel_非常长的内容描述包含了很多技术细节和详细说明',
            'url': 'https://x.com/samuel/status/1976062342451667233'
        }
    ]
    
    print("🔍 Testing Current Byte Lengths")
    print("=" * 80)
    print("📌 CURRENT PROBLEM: Files are over 255 bytes")
    print("🎯 TARGET: Around 150 bytes (±20)")
    print("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   Input: {case['title']}")
        
        # Test both formats
        if case['url']:
            # Standardized format (with URL)
            result = create_standardized_filename(case['title'], case['url'], max_length=200)
            result_with_ext = f"{result}.html"
            byte_length = len(result_with_ext.encode('utf-8'))
            print(f"   Standardized: {result_with_ext}")
            print(f"   Length: {byte_length} bytes {'❌ OVER 255!' if byte_length > 255 else '✅ Under 255'}")
        else:
            # Enhanced content format (no URL)
            result = create_enhanced_content_filename(case['title'], max_length=220)
            result_with_ext = f"{result}.html"
            byte_length = len(result_with_ext.encode('utf-8'))
            print(f"   Enhanced: {result_with_ext}")
            print(f"   Length: {byte_length} bytes {'❌ OVER 255!' if byte_length > 255 else '✅ Under 255'}")
        
        # Show what 150-byte target would look like
        target_150 = create_enhanced_content_filename(case['title'], max_length=150)
        target_150_with_ext = f"{target_150}.html"
        target_byte_length = len(target_150_with_ext.encode('utf-8'))
        print(f"   At 150: {target_150_with_ext}")
        print(f"   Length: {target_byte_length} bytes {'🎯 TARGET RANGE!' if 130 <= target_byte_length <= 170 else '📏 Outside target'}")

if __name__ == "__main__":
    test_current_lengths()