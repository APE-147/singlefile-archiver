#!/usr/bin/env python3
"""
Convenience script to run the filename optimization command.

This script demonstrates the correct ways to run the optimization command
after fixing the module import issues.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the filename optimization command with proper setup."""
    
    # Method 1: Using the installed package (recommended)
    print("=== Method 1: Using installed package ===")
    print("Run: FF_BATCH_PROCESSING=true python -m singlefile_archiver.commands.optimize /path/to/archive --dry-run")
    print()
    
    # Method 2: Using the CLI script if available
    print("=== Method 2: Using CLI script ===") 
    print("Run: singlefile-archiver optimize /path/to/archive --dry-run")
    print("Note: This requires FF_BATCH_PROCESSING=true environment variable")
    print()
    
    # Method 3: Running this convenience script
    if len(sys.argv) > 1:
        archive_path = sys.argv[1]
        dry_run = "--dry-run" if "--dry-run" in sys.argv else ""
        
        print(f"=== Running optimization on: {archive_path} ===")
        
        # Set the feature flag
        env = os.environ.copy()
        env['FF_BATCH_PROCESSING'] = 'true'
        
        # Run the command
        cmd = [
            sys.executable, "-m", "singlefile_archiver.commands.optimize",
            archive_path
        ]
        if dry_run:
            cmd.append("--dry-run")
            
        try:
            result = subprocess.run(cmd, env=env, check=True)
            print(f"Command completed successfully with exit code: {result.returncode}")
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code: {e.returncode}")
            sys.exit(e.returncode)
    else:
        print("=== Usage ===")
        print("python run_optimize.py /path/to/archive [--dry-run]")
        print()
        print("Example:")
        print("python run_optimize.py /Users/niceday/Developer/Cloud/Dropbox/-File-/Archive/Web --dry-run")

if __name__ == "__main__":
    main()