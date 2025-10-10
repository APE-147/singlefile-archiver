#!/usr/bin/env python3
"""Debug script to test docker service filename generation logic."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.services.docker_service import DockerService

def test_filename_generation():
    """Test the filename generation logic with problematic titles."""
    
    # Set up environment
    os.environ['FF_FILENAME_OPTIMIZATION'] = 'true'
    os.environ['FF_ENHANCED_CONTENT_NAMING'] = 'true'
    
    # Create docker service instance
    docker_service = DockerService()
    
    # Test cases from user report
    test_cases = [
        {
            'title': 'X_上的_宝玉："OpenAI_新的产品_ChatGPT功能详细解析和使用指南',
            'url': 'https://x.com/baozhu/status/123456',
            'expected_pattern': 'X_上的_宝玉_OpenAI新的产品ChatGPT功能详细解析'
        },
        {
            'title': 'X_上的_泊舟："今天，我在和一个大学生聊天时发现',
            'url': 'https://x.com/bozhou/status/789012',
            'expected_pattern': 'X_上的_泊舟_今天我在和一个大学生聊天时发现'
        },
        {
            'title': 'X_上的_宝玉："麦肯锡调研了50个基于AI的创业公司',
            'url': 'https://x.com/baozhu/status/345678',
            'expected_pattern': 'X_上的_宝玉_麦肯锡调研了50个基于AI的创业公司'
        }
    ]
    
    output_dir = Path("/tmp/test_output")
    output_dir.mkdir(exist_ok=True)
    
    print("🔍 Testing Docker Service Filename Generation")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}:")
        print(f"  Title: {case['title']}")
        print(f"  URL: {case['url']}")
        
        try:
            # Test the _derive_output_file method
            result_path = docker_service._derive_output_file(
                url=case['url'],
                html_content=f"<title>{case['title']}</title>",
                output_dir=output_dir
            )
            
            result_filename = result_path.name
            print(f"  Generated: {result_filename}")
            print(f"  Length: {len(result_filename.encode('utf-8'))} bytes")
            
            # Check if it matches expected pattern
            if case['expected_pattern'] in result_filename:
                print(f"  ✅ Contains expected content: {case['expected_pattern']}")
            else:
                print(f"  ❌ Missing expected content: {case['expected_pattern']}")
                
        except Exception as e:
            print(f"  💥 Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 Testing Environment Variables:")
    print(f"  FF_FILENAME_OPTIMIZATION: {os.getenv('FF_FILENAME_OPTIMIZATION')}")
    print(f"  FF_ENHANCED_CONTENT_NAMING: {os.getenv('FF_ENHANCED_CONTENT_NAMING')}")
    
    # Test the flags logic directly
    use_optimization = os.getenv('FF_FILENAME_OPTIMIZATION', 'false').lower() == 'true'
    use_enhanced_naming = os.getenv('FF_ENHANCED_CONTENT_NAMING', 'true').lower() == 'true'
    
    print(f"  use_optimization: {use_optimization}")
    print(f"  use_enhanced_naming: {use_enhanced_naming}")
    print(f"  Should use enhanced: {use_optimization and use_enhanced_naming}")


if __name__ == "__main__":
    test_filename_generation()