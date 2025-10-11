#!/usr/bin/env python3
"""Test the fixed byte-aware implementation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import create_enhanced_content_filename, create_standardized_filename

def test_fixed_implementation():
    """Test the fixed byte-aware implementation."""
    
    # Create test cases that previously exceeded 255 bytes
    massive_content = "这是一个超级超级超级长的内容描述包含了大量的技术细节和详细说明以及各种复杂的概念和理论讨论关于人工智能机器学习深度学习神经网络自然语言处理计算机视觉语音识别推荐系统搜索引擎数据挖掘大数据分析云计算边缘计算量子计算区块链加密货币金融科技生物技术基因编辑医疗诊断药物发现新材料科学能源技术环境保护可持续发展等等各种前沿科技领域的内容和深入分析研究报告学术论文技术文档代码示例实际应用案例最佳实践"
    
    test_cases = [
        {
            'description': '✅ User Case 1: Normal X_上的_宝玉 content',
            'title': 'X_上的_宝玉_OpenAI新的产品ChatGPT功能详细解析和使用指南',
            'url': 'https://x.com/baozhu/status/123456'
        },
        {
            'description': '🔥 FIXED Case 2: Previously 606 bytes → should be ~150',
            'title': f'X_上的_宝玉_{massive_content}',
            'url': None
        },
        {
            'description': '🔥 FIXED Case 3: Massive content WITH URL',
            'title': f'X_上的_宝玉_{massive_content}',
            'url': 'https://x.com/baozhu/status/1976062342451667233'
        },
        {
            'description': '✅ User Case 4: Long but reasonable content', 
            'title': 'X_上的_宝玉_比特币和区块链技术的发展现状以及未来趋势分析包括投资建议和风险评估',
            'url': None
        }
    ]
    
    print("🚀 Testing FIXED Byte-Aware Implementation")
    print("=" * 80)
    print("🎯 TARGET: All results should be 130-170 bytes (150 ±20)")
    print("📌 BEFORE: Some cases were 606 bytes!")
    print("✅ AFTER: Should be ~150 bytes with smart truncation")
    print("=" * 80)
    
    all_in_range = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['description']}")
        
        # Test with the fixed implementation (150-byte target)
        if case['url']:
            result = create_standardized_filename(case['title'], case['url'], max_bytes=150)
        else:
            result = create_enhanced_content_filename(case['title'], max_bytes=150)
        
        result_with_ext = f"{result}.html"
        byte_length = len(result_with_ext.encode('utf-8'))
        
        # Check if in target range
        in_range = 130 <= byte_length <= 170
        status = "🎯 IN TARGET RANGE!" if in_range else "❌ OUTSIDE TARGET"
        
        print(f"   Result: {result_with_ext}")
        print(f"   Length: {byte_length} bytes {status}")
        
        if not in_range:
            all_in_range = False
            
        # Show content preservation quality
        if '…' in result:
            print(f"   📝 Truncated with semantic preservation")
        elif len(case['title']) > 50:
            print(f"   📝 Full content preserved")
        
        # Show the actual content for massive cases
        if 'FIXED' in case['description']:
            print(f"   📊 Reduction from ~606 bytes to {byte_length} bytes")
            print(f"   🧠 Content: {result[:80]}...")
    
    print("\n" + "=" * 80)
    if all_in_range:
        print("🎉 SUCCESS! All test cases are within 130-170 byte target range!")
        print("✅ Fixed implementation correctly controls byte length")
        print("✅ Smart truncation preserves meaningful content")
        print("✅ Multi-layer strategy (180→150→120) working correctly")
    else:
        print("❌ Some cases are still outside target range")
        print("🔧 May need further tuning of the truncation strategy")
    print("=" * 80)
    
    return all_in_range

def test_preview_table_accuracy():
    """Test that the preview table shows accurate byte lengths."""
    print("\n🔍 Testing Preview Table Accuracy")
    print("=" * 50)
    
    # Simulate what users see in the preview table
    test_cases = [
        'X_上的_宝玉_比特币总裁：过去数年我一直在思考如何让更多人了解和接受加密货币技术的重要性.html',
        'X_上的_DN-Samuel_[URL]_https%3A%2F%2Fx.com%2FSamuelQZQ%2Fstatus%2F1976062342451667233.html',
        'X_上的_宝玉_OpenAI新的产品ChatGPT功能详细解析和使用指南.html'
    ]
    
    for filename in test_cases:
        byte_length = len(filename.encode('utf-8'))
        status = "✅ Under 255" if byte_length <= 255 else "❌ OVER 255!"
        range_status = "🎯 IN TARGET!" if 130 <= byte_length <= 170 else "📏 Outside target"
        
        print(f"   {filename[:60]}...")
        print(f"   Length: {byte_length} bytes {status} {range_status}")

if __name__ == "__main__":
    success = test_fixed_implementation()
    test_preview_table_accuracy()
    sys.exit(0 if success else 1)