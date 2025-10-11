#!/usr/bin/env python3
"""Test the exact cases reported by the user to verify the fix."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.services.docker_service import DockerService

def test_user_reported_cases():
    """Test the exact cases the user reported as problematic."""
    
    # Set up environment  
    os.environ['FF_FILENAME_OPTIMIZATION'] = 'true'
    os.environ['FF_ENHANCED_CONTENT_NAMING'] = 'true'
    
    # Create docker service instance
    docker_service = DockerService()
    
    # User's exact reported cases
    user_cases = [
        {
            'description': 'Case 1: 宝玉 - OpenAI content',
            'title': 'X_上的_宝玉："OpenAI_新的产品_ChatGPT功能详细解析和使用指南',
            'url': 'https://x.com/baozhu/status/123456',
            'expected_contains': ['X_上的_宝玉', 'OpenAI', '新的产品', 'ChatGPT'],
            'should_not_contain': ['Web_上的_Content', '[URL]', 'https%3A']
        },
        {
            'description': 'Case 2: 泊舟 - university chat content',
            'title': 'X_上的_泊舟："今天，我在和一个大学生聊天时发现',
            'url': 'https://x.com/bozhou/status/789012', 
            'expected_contains': ['X_上的_泊舟', '今天', '大学生', '聊天'],
            'should_not_contain': ['Web_上的_Content', '[URL]', 'https%3A']
        },
        {
            'description': 'Case 3: 宝玉 - McKinsey AI research',
            'title': 'X_上的_宝玉："麦肯锡调研了50个基于AI的创业公司',
            'url': 'https://x.com/baozhu/status/345678',
            'expected_contains': ['X_上的_宝玉', '麦肯锡', 'AI', '创业公司'],
            'should_not_contain': ['Web_上的_Content', '[URL]', 'https%3A']
        }
    ]
    
    output_dir = Path("/tmp/test_output")
    output_dir.mkdir(exist_ok=True)
    
    print("🔍 Testing User Reported Cases - Fixed Implementation")
    print("=" * 70)
    print("❌ BEFORE: Generic output like 'Web_上的_Content_X_073.html'")
    print("✅ AFTER: Enhanced content like 'X_上的_宝玉_OpenAI新的产品ChatGPT...'")
    print("=" * 70)
    
    all_passed = True
    
    for i, case in enumerate(user_cases, 1):
        print(f"\n🧪 {case['description']}")
        print(f"   Input: {case['title']}")
        
        try:
            # Test the _derive_output_file method
            result_path = docker_service._derive_output_file(
                url=case['url'],
                html_content=f"<title>{case['title']}</title>",
                output_dir=output_dir
            )
            
            result_filename = result_path.name
            print(f"   Output: {result_filename}")
            print(f"   Length: {len(result_filename.encode('utf-8'))} bytes")
            
            # Test expected content
            case_passed = True
            for expected in case['expected_contains']:
                if expected in result_filename:
                    print(f"   ✅ Contains: '{expected}'")
                else:
                    print(f"   ❌ Missing: '{expected}'")
                    case_passed = False
            
            # Test should not contain
            for not_expected in case['should_not_contain']:
                if not_expected not in result_filename:
                    print(f"   ✅ Correctly excludes: '{not_expected}'")
                else:
                    print(f"   ❌ Incorrectly contains: '{not_expected}'")
                    case_passed = False
            
            # Check byte length is reasonable
            byte_length = len(result_filename.encode('utf-8'))
            if 50 <= byte_length <= 255:
                print(f"   ✅ Length reasonable: {byte_length} bytes")
            else:
                print(f"   ⚠️  Length concern: {byte_length} bytes (expected 50-255)")
                
            if case_passed:
                print(f"   🎉 CASE PASSED")
            else:
                print(f"   💥 CASE FAILED")
                all_passed = False
                
        except Exception as e:
            print(f"   💥 Error: {e}")
            all_passed = False
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL USER CASES PASSED! The fix is working correctly.")
        print("✅ Enhanced content preservation is now functioning as expected.")
    else:
        print("❌ Some cases failed. Additional debugging needed.")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = test_user_reported_cases()
    sys.exit(0 if success else 1)