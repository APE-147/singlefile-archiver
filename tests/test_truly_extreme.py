#!/usr/bin/env python3
"""Test truly extreme cases that will definitely exceed 255 bytes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import create_enhanced_content_filename, create_standardized_filename, _semantic_truncate

def test_truly_extreme():
    """Test truly extreme cases with very long content to force >255 bytes."""
    
    # Create cases that will definitely be >255 bytes
    massive_content = "这是一个超级超级超级长的内容描述包含了大量的技术细节和详细说明以及各种复杂的概念和理论讨论关于人工智能机器学习深度学习神经网络自然语言处理计算机视觉语音识别推荐系统搜索引擎数据挖掘大数据分析云计算边缘计算量子计算区块链加密货币金融科技生物技术基因编辑医疗诊断药物发现新材料科学能源技术环境保护可持续发展等等各种前沿科技领域的内容和深入分析研究报告学术论文技术文档代码示例实际应用案例最佳实践"
    
    extreme_cases = [
        {
            'description': 'MASSIVE 1: Truly massive content - should trigger truncation',
            'title': f'X_上的_宝玉_{massive_content}',
            'url': None
        },
        {
            'description': 'MASSIVE 2: Massive content WITH URL',
            'title': f'X_上的_宝玉_{massive_content}',
            'url': 'https://x.com/baozhu/status/1976062342451667233'
        },
        {
            'description': 'MASSIVE 3: Force max_length=400 to see what happens', 
            'title': f'X_上的_宝玉_{massive_content}',
            'url': None,
            'force_max_length': 400
        }
    ]
    
    print("🚀 Testing TRULY EXTREME Cases - Force >255 bytes")
    print("=" * 80)
    print("📌 GOAL: Create cases that DEFINITELY exceed 255 bytes")
    print("🎯 TARGET: Show the difference between 220 and 150 byte limits")
    print("=" * 80)
    
    for i, case in enumerate(extreme_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   Input length: {len(case['title'])} chars")
        
        # Test current max_length (220 for content, 200 for URL)
        if case['url']:
            current_max = 200
            result_current = create_standardized_filename(case['title'], case['url'], max_length=current_max)
        else:
            current_max = case.get('force_max_length', 220)
            result_current = create_enhanced_content_filename(case['title'], max_length=current_max)
        
        result_current_with_ext = f"{result_current}.html"
        current_bytes = len(result_current_with_ext.encode('utf-8'))
        
        print(f"   CURRENT ({current_max}): {result_current_with_ext[:100]}...")
        print(f"   Length: {current_bytes} bytes {'❌ OVER 255!' if current_bytes > 255 else '✅ Under 255'}")
        
        # Test target 150 setting
        if case['url']:
            result_target = create_standardized_filename(case['title'], case['url'], max_length=150)
        else:
            result_target = create_enhanced_content_filename(case['title'], max_length=150)
            
        result_target_with_ext = f"{result_target}.html"
        target_bytes = len(result_target_with_ext.encode('utf-8'))
        
        print(f"   TARGET (150): {result_target_with_ext[:100]}...")
        print(f"   Length: {target_bytes} bytes {'🎯 IN TARGET!' if 130 <= target_bytes <= 170 else '📏 Outside target'}")
        
        # Show reduction
        reduction = current_bytes - target_bytes
        print(f"   📉 Reduction: {reduction} bytes ({'saved' if reduction > 0 else 'none'})")
        
        # Test semantic truncation directly
        print(f"   🧠 Testing semantic truncation at 150 chars:")
        semantic_result = _semantic_truncate(massive_content, 150)
        print(f"        Truncated: {semantic_result[:80]}...")
        print(f"        Length: {len(semantic_result)} chars")

def test_byte_vs_char_length():
    """Test the difference between character length and byte length for Chinese text."""
    print("\n" + "=" * 80)
    print("🔤 Testing Character vs Byte Length for Chinese Text")
    print("=" * 80)
    
    test_strings = [
        "X_上的_宝玉_",  # Base format
        "X_上的_宝玉_比特币",  # With some Chinese content  
        "X_上的_宝玉_比特币和区块链技术的发展现状",  # Longer Chinese content
        "X_上的_宝玉_[URL]_https%3A%2F%2Fx.com",  # With URL
    ]
    
    for test_str in test_strings:
        char_len = len(test_str)
        byte_len = len(test_str.encode('utf-8'))
        print(f"   '{test_str}'")
        print(f"   Characters: {char_len}, Bytes: {byte_len} (ratio: {byte_len/char_len:.2f})")

if __name__ == "__main__":
    test_truly_extreme()
    test_byte_vs_char_length()