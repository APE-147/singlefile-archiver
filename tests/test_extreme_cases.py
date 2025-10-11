#!/usr/bin/env python3
"""Test extreme cases that might produce 255+ byte filenames."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import create_enhanced_content_filename, create_standardized_filename

def test_extreme_cases():
    """Test extreme cases that might go over 255 bytes."""
    
    # Test cases designed to produce long filenames
    extreme_cases = [
        {
            'description': 'EXTREME 1: Very long content description',
            'title': 'X_上的_宝玉_这是一个非常非常长的内容描述包含了大量的技术细节和详细说明以及各种复杂的概念和理论讨论关于人工智能机器学习深度学习神经网络等等各种前沿科技领域的内容',
            'url': None
        },
        {
            'description': 'EXTREME 2: Very long content WITH URL',
            'title': 'X_上的_宝玉_这是一个非常非常长的内容描述包含了大量的技术细节和详细说明以及各种复杂的概念和理论讨论关于人工智能机器学习深度学习神经网络等等各种前沿科技领域的内容',
            'url': 'https://x.com/baozhu/status/1976062342451667233234567890123456789'
        },
        {
            'description': 'EXTREME 3: Long username + long content',
            'title': 'X_上的_非常长的用户名包含很多字符_这是一个非常详细的内容描述包含了技术分析和深入讨论',
            'url': 'https://x.com/verylongusernamethatgoesforever/status/1976062342451667233'
        },
        {
            'description': 'EXTREME 4: Current 220 vs target 150',
            'title': 'X_上的_宝玉_比特币和区块链技术的发展现状以及未来趋势分析包括投资建议和风险评估以及监管政策的影响和市场前景预测',
            'url': None
        }
    ]
    
    print("🔥 Testing EXTREME Cases - Looking for 255+ byte cases")
    print("=" * 80)
    print("📌 GOAL: Find cases that produce >255 bytes to fix")
    print("🎯 TARGET: Reduce to ~150 bytes")
    print("=" * 80)
    
    for i, case in enumerate(extreme_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   Input: {case['title'][:80]}...")
        
        # Test current settings
        if case['url']:
            # Standardized format (with URL) - max_length=200
            result_current = create_standardized_filename(case['title'], case['url'], max_length=200)
        else:
            # Enhanced content format (no URL) - max_length=220  
            result_current = create_enhanced_content_filename(case['title'], max_length=220)
        
        result_current_with_ext = f"{result_current}.html"
        current_bytes = len(result_current_with_ext.encode('utf-8'))
        
        print(f"   CURRENT (220): {result_current_with_ext}")
        print(f"   Length: {current_bytes} bytes {'❌ OVER 255!' if current_bytes > 255 else '✅ Under 255'}")
        
        # Test target 150 setting
        if case['url']:
            result_target = create_standardized_filename(case['title'], case['url'], max_length=150)
        else:
            result_target = create_enhanced_content_filename(case['title'], max_length=150)
            
        result_target_with_ext = f"{result_target}.html"
        target_bytes = len(result_target_with_ext.encode('utf-8'))
        
        print(f"   TARGET (150): {result_target_with_ext}")
        print(f"   Length: {target_bytes} bytes {'🎯 IN TARGET!' if 130 <= target_bytes <= 170 else '📏 Outside target'}")
        
        # Show reduction
        reduction = current_bytes - target_bytes
        print(f"   📉 Reduction: {reduction} bytes ({'saved' if reduction > 0 else 'none'})")

if __name__ == "__main__":
    test_extreme_cases()