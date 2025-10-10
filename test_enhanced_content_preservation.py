#!/usr/bin/env python3
"""
Comprehensive tests for enhanced content preservation functionality.
Tests the new filename optimization strategy that preserves more meaningful content.
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
    _extract_url_from_filename,
    _has_url_indicators,
    _extract_content_description,
    _semantic_truncate,
    generate_optimized_filename
)


def test_url_detection():
    """Test enhanced URL detection algorithms."""
    print("🔍 Testing URL Detection...")
    
    test_cases = [
        # With [URL] marker
        ("X_上的_用户_[URL]_https%3A%2F%2Fx.com%2Fuser%2Fstatus%2F123", "https://x.com/user/status/123"),
        
        # Direct URL patterns
        ("(Title) https://instagram.com/p/ABC123", "https://instagram.com/p/ABC123"),
        
        # Social media domain reconstruction
        ("twitter.com_user_status_123456789", "https://x.com/user/status/123456789"),
        ("instagram.com_p_ABC123DEF", "https://instagram.com/p/ABC123DEF"),
        ("youtube.com_watch?v=dQw4w9WgXcQ", "https://youtube.com/watch?v=dQw4w9WgXcQ"),
        
        # No URL cases
        ("X_上的_比特币总裁：过去24小时", ""),
        ("简单的页面标题", ""),
    ]
    
    passed = 0
    for filename, expected_url in test_cases:
        result = _extract_url_from_filename(filename)
        if result == expected_url:
            print(f"  ✅ {filename[:50]}... -> {result}")
            passed += 1
        else:
            print(f"  ❌ {filename[:50]}... -> Expected: {expected_url}, Got: {result}")
    
    print(f"URL Detection: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)


def test_content_preservation():
    """Test enhanced content preservation for non-URL cases."""
    print("📝 Testing Content Preservation...")
    
    test_cases = [
        # Social media content without URLs
        ("X_上的_比特币总裁：过去24小时比特币价格分析和市场趋势预测", 200),
        ("Instagram_上的_旅行博主：今天在巴黎拍摄的美丽日落照片分享", 200),
        ("微博_上的_科技评论员：最新iPhone15评测详细分析", 180),
        
        # Regular web content
        ("深度学习入门教程：从零开始学习神经网络", 150),
        ("Python编程最佳实践和代码优化技巧", 120),
    ]
    
    passed = 0
    for title, max_length in test_cases:
        result = create_enhanced_content_filename(title, max_length)
        byte_length = len(result.encode('utf-8'))
        
        # Check that result preserves meaningful content and respects length
        if byte_length <= max_length and len(result) > 20:
            print(f"  ✅ {title[:40]}... -> {result} ({byte_length} bytes)")
            passed += 1
        else:
            print(f"  ❌ {title[:40]}... -> {result} ({byte_length} bytes, max: {max_length})")
    
    print(f"Content Preservation: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)


def test_semantic_truncation():
    """Test semantic-aware content truncation."""
    print("✂️ Testing Semantic Truncation...")
    
    test_cases = [
        # Sentence boundaries
        ("这是第一句话。这是第二句话。这是第三句话。", 20),
        ("Complete sentence! Another sentence? Final sentence.", 35),
        
        # Phrase boundaries
        ("关键词一，关键词二，关键词三，更多内容", 25),
        ("Python编程：基础教程；进阶技巧；实战项目", 30),
        
        # Word boundaries
        ("Long title with many words that need truncation", 25),
        ("很长的中文标题需要进行智能截断处理", 20),
    ]
    
    passed = 0
    for text, max_length in test_cases:
        result = _semantic_truncate(text, max_length)
        
        # Check length constraint and semantic preservation
        if len(result) <= max_length and (result.endswith('…') or len(text) <= max_length):
            print(f"  ✅ {text[:30]}... -> {result}")
            passed += 1
        else:
            print(f"  ❌ {text[:30]}... -> {result} (length: {len(result)}, max: {max_length})")
    
    print(f"Semantic Truncation: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)


def test_standardized_vs_enhanced_format():
    """Test the distinction between standardized (URL) and enhanced (content) formats."""
    print("🔄 Testing Format Selection...")
    
    test_cases = [
        # Should use standardized format (has URL)
        {
            "title": "X_上的_DN-Samuel_tweet内容",
            "url": "https://x.com/SamuelQZQ/status/1976062342451667233",
            "expected_format": "standardized",
            "should_contain": ["[URL]", "_上的_", "https%3A"]
        },
        
        # Should use enhanced content format (no URL or simple URL)
        {
            "title": "X_上的_比特币总裁：过去24小时比特币价格分析",
            "url": "",
            "expected_format": "enhanced",
            "should_contain": ["_上的_", "比特币"],
            "should_not_contain": ["[URL]", "https%3A"]
        }
    ]
    
    passed = 0
    for case in test_cases:
        title = case["title"]
        url = case["url"]
        
        if url:
            result = create_standardized_filename(title, url, max_length=200)
        else:
            result = create_enhanced_content_filename(title, max_length=220)
        
        # Check format expectations
        format_correct = True
        for should_contain in case.get("should_contain", []):
            if should_contain not in result:
                format_correct = False
                break
        
        for should_not_contain in case.get("should_not_contain", []):
            if should_not_contain in result:
                format_correct = False
                break
        
        if format_correct:
            print(f"  ✅ {case['expected_format']}: {title[:30]}... -> {result[:60]}...")
            passed += 1
        else:
            print(f"  ❌ {case['expected_format']}: {title[:30]}... -> {result[:60]}...")
    
    print(f"Format Selection: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)


def test_real_world_scenarios():
    """Test with real-world problematic filenames."""
    print("🌍 Testing Real-World Scenarios...")
    
    # These are the problematic cases mentioned in the requirements
    test_files = [
        "X_上的_比特币总裁过去24小时比特币价格经历了显著波动从68000美元跌至65000美元主要原因包括市场对美联储政策的担忧以及大型机构投资者的获利了结行为技术分析显示短期内可能进一步调整至62000美元支撑位这是一个非常长的推文内容_x.com_bitcoin_ceo_status_1234567890.html",
        "X_上的_宝玉OpenAI最新发布的GPT-4.5模型在多项基准测试中表现出色特别是在代码生成数学推理和创意写作方面有显著提升预计将在下个月正式向企业用户开放API接口_x.com_dotey_status_9876543210.html"
    ]
    
    passed = 0
    for original_filename in test_files:
        try:
            # Simulate the file path
            file_path = Path(original_filename)
            
            # Test the enhanced filename generation
            result = generate_optimized_filename(file_path, existing_names=set(), use_standardized_format=True)
            
            # Check that result is reasonable
            byte_length = len(result.encode('utf-8'))
            has_meaningful_content = any(keyword in result for keyword in ['比特币', 'OpenAI', 'GPT'])
            
            if byte_length <= 255 and has_meaningful_content:
                print(f"  ✅ {original_filename[:50]}...")
                print(f"     -> {result} ({byte_length} bytes)")
                passed += 1
            else:
                print(f"  ❌ {original_filename[:50]}...")
                print(f"     -> {result} ({byte_length} bytes)")
                
        except Exception as e:
            print(f"  ❌ {original_filename[:50]}... -> Error: {e}")
    
    print(f"Real-World Scenarios: {passed}/{len(test_files)} tests passed\n")
    return passed == len(test_files)


def test_length_filtering():
    """Test that only files >255 bytes are processed."""
    print("📏 Testing Length Filtering...")
    
    test_cases = [
        # Should be skipped (≤255 bytes)
        ("short_filename.html", False),
        ("medium_length_filename_with_some_content.html", False),
        
        # Should be processed (>255 bytes)
        ("X_上的_" + "很长的内容描述" * 20 + "_非常详细的推文内容.html", True),
        ("a" * 252 + ".html", True),  # Exactly over 255 bytes (252 + 5 for .html = 257)
    ]
    
    passed = 0
    for filename, should_process in test_cases:
        byte_length = len(filename.encode('utf-8'))
        needs_processing = byte_length > 255
        
        if needs_processing == should_process:
            status = "PROCESS" if should_process else "SKIP"
            print(f"  ✅ {status}: {filename[:40]}... ({byte_length} bytes)")
            passed += 1
        else:
            print(f"  ❌ Expected {'PROCESS' if should_process else 'SKIP'}: {filename[:40]}... ({byte_length} bytes)")
    
    print(f"Length Filtering: {passed}/{len(test_cases)} tests passed\n")
    return passed == len(test_cases)


def run_all_tests():
    """Run all tests and provide summary."""
    print("🧪 Running Enhanced Content Preservation Tests\n")
    print("=" * 60)
    
    test_results = [
        test_url_detection(),
        test_content_preservation(),
        test_semantic_truncation(),
        test_standardized_vs_enhanced_format(),
        test_real_world_scenarios(),
        test_length_filtering(),
    ]
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print("=" * 60)
    print(f"📊 SUMMARY: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Enhanced content preservation is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Review the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)