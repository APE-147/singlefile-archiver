#!/usr/bin/env python3
"""Debug script to trace step by step the filename generation."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from singlefile_archiver.commands.optimize import (
    _extract_platform_info, 
    _extract_content_description,
    _semantic_truncate
)

def debug_step_by_step():
    """Debug the content filename generation step by step."""
    
    title = 'X_上的_宝玉："OpenAI_新的产品_ChatGPT功能详细解析和使用指南'
    
    print("🔍 Step-by-Step Debug of Enhanced Content Generation")
    print("=" * 60)
    print(f"Input title: {title}")
    print()
    
    # Step 1: Extract platform info
    print("📍 Step 1: Extract platform info")
    platform_info = _extract_platform_info(title)
    print(f"  Platform info: {platform_info}")
    
    if platform_info:
        platform = platform_info['platform']
        user = platform_info['user']
        print(f"  Platform: {platform}")
        print(f"  User: {user}")
        
        # Step 2: Extract content description
        print("\n📍 Step 2: Extract content description")
        content_desc = _extract_content_description(title, platform_info)
        print(f"  Content description: '{content_desc}'")
        
        # Step 3: Build base format
        print("\n📍 Step 3: Build base format")
        base_format = f"{platform}_上的_{user}_"
        print(f"  Base format: '{base_format}'")
        
        # Step 4: Calculate available space
        max_length = 220
        available_for_content = max_length - len(base_format)
        print(f"  Max length: {max_length}")
        print(f"  Base format length: {len(base_format)}")
        print(f"  Available for content: {available_for_content}")
        
        # Step 5: Semantic truncation
        if available_for_content > 20:
            print("\n📍 Step 5: Semantic truncation")
            truncated_content = _semantic_truncate(content_desc, available_for_content)
            print(f"  Truncated content: '{truncated_content}'")
            
            # Step 6: Final assembly
            print("\n📍 Step 6: Final assembly")
            enhanced = f"{base_format}{truncated_content}"
            print(f"  Final result: '{enhanced}'")
            print(f"  Final length: {len(enhanced.encode('utf-8'))} bytes")
        else:
            print("\n📍 Step 5: Fallback (limited space)")
            enhanced = f"{platform}_上的_{user}"
            print(f"  Fallback result: '{enhanced}'")
            
    else:
        print("  No platform info found - would use fallback logic")

if __name__ == "__main__":
    debug_step_by_step()