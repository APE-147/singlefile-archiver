#!/usr/bin/env python3
"""Debug script to test the enhanced content function directly."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import create_enhanced_content_filename, _has_url_indicators

def test_enhanced_content_function():
    """Test the enhanced content function directly."""
    
    # Test cases from user report
    test_cases = [
        'X_上的_宝玉："OpenAI_新的产品_ChatGPT功能详细解析和使用指南',
        'X_上的_泊舟："今天，我在和一个大学生聊天时发现',
        'X_上的_宝玉："麦肯锡调研了50个基于AI的创业公司'
    ]
    
    print("🔍 Testing Enhanced Content Function Directly")
    print("=" * 60)
    
    for i, title in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}:")
        print(f"  Title: {title}")
        
        # Test URL indicators
        has_url = _has_url_indicators(title)
        print(f"  Has URL indicators: {has_url}")
        
        # Test enhanced content function
        try:
            result = create_enhanced_content_filename(title, max_length=220)
            print(f"  Enhanced result: {result}")
            print(f"  Length: {len(result.encode('utf-8'))} bytes")
            
            if "宝玉" in title and "宝玉" in result:
                print(f"  ✅ Contains user: 宝玉")
            elif "泊舟" in title and "泊舟" in result:
                print(f"  ✅ Contains user: 泊舟")
            
            if "OpenAI" in title and "openai" in result.lower():
                print(f"  ✅ Contains content: OpenAI")
            elif "今天" in title and "今天" in result:
                print(f"  ✅ Contains content: 今天")
            elif "麦肯锡" in title and "麦肯锡" in result:
                print(f"  ✅ Contains content: 麦肯锡")
                
        except Exception as e:
            print(f"  💥 Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_content_function()