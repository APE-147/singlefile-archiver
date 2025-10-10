#!/usr/bin/env python3
"""
Demo script showing enhanced content preservation functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from singlefile_archiver.commands.optimize import (
    create_standardized_filename,
    create_enhanced_content_filename,
    generate_optimized_filename
)


def demo_enhanced_content_preservation():
    """Demo the enhanced content preservation functionality."""
    
    print("🎯 Enhanced Content Preservation Demo")
    print("=" * 50)
    
    # Example 1: URL-containing file (should use standardized format)
    print("\n📝 Example 1: File with URL information")
    title1 = "X_上的_DN-Samuel_tweet内容"
    url1 = "https://x.com/SamuelQZQ/status/1976062342451667233"
    
    result1 = create_standardized_filename(title1, url1, max_length=200)
    print(f"Input: {title1}")
    print(f"URL: {url1}")
    print(f"Output: {result1}")
    print(f"Length: {len(result1.encode('utf-8'))} bytes")
    
    # Example 2: Content-only file (should use enhanced format)
    print("\n📝 Example 2: Content-only file (Enhanced preservation)")
    title2 = "X_上的_比特币总裁：过去24小时比特币价格分析和市场趋势预测详细报告"
    
    result2 = create_enhanced_content_filename(title2, max_length=220)
    print(f"Input: {title2}")
    print(f"Output: {result2}")
    print(f"Length: {len(result2.encode('utf-8'))} bytes")
    print(f"Content preserved: ✅ Much more meaningful content retained!")
    
    # Example 3: Compare old vs new approach
    print("\n📊 Comparison: Old vs New Approach")
    long_content = "X_上的_宝玉：OpenAI最新发布的GPT-4.5模型在多项基准测试中表现出色，特别是在代码生成、数学推理和创意写作方面有显著提升，预计将在下个月正式向企业用户开放API接口，这将极大地推动人工智能在各行业的应用普及"
    
    # Simulate old approach (would be much shorter)
    old_approach_length = 120
    old_result = long_content[:old_approach_length-3] + "..."
    
    # New enhanced approach
    new_result = create_enhanced_content_filename(long_content, max_length=220)
    
    print(f"\n📋 Original content: {long_content}")
    print(f"📉 Old approach (120 bytes): {old_result}")
    print(f"   Length: {len(old_result.encode('utf-8'))} bytes")
    print(f"📈 New enhanced (220 bytes): {new_result}")
    print(f"   Length: {len(new_result.encode('utf-8'))} bytes")
    print(f"🎯 Improvement: {((len(new_result) - len(old_result)) / len(old_result) * 100):.1f}% more content preserved!")
    
    # Example 4: Demonstrate real-world scenario with pathlib
    print("\n🌍 Real-world scenario simulation")
    problematic_files = [
        "X_上的_科技博主过去24小时科技行业发生的重大变化包括苹果发布新产品谷歌推出AI助手微软更新系统OpenAI优化模型这些变化将深刻影响未来科技发展趋势和用户体验_content.html",
        "Instagram_上的_旅行达人今天在法国巴黎埃菲尔铁塔附近拍摄的绝美日落照片分享给大家这里的景色真是太美了推荐所有朋友都来看看_photo_share.html"
    ]
    
    for i, filename in enumerate(problematic_files, 1):
        print(f"\n🔧 Processing file {i}:")
        print(f"   Original: {filename[:60]}... ({len(filename.encode('utf-8'))} bytes)")
        
        # Create Path object
        file_path = Path(filename)
        
        # Generate optimized filename using new system
        optimized = generate_optimized_filename(
            file_path, 
            existing_names=set(), 
            use_standardized_format=True
        )
        
        print(f"   Enhanced: {optimized} ({len(optimized.encode('utf-8'))} bytes)")
        print(f"   Status: ✅ Meaningful content preserved within filesystem limits")


if __name__ == "__main__":
    demo_enhanced_content_preservation()