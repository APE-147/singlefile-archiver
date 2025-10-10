# Module Import Fix for singlefile_archiver

## Problem Fixed
Users were getting `ModuleNotFoundError: No module named 'singlefile_archiver'` when trying to run:
```bash
python -m singlefile_archiver.commands.optimize /path/to/archive --dry-run
```

## Root Causes & Solutions

### 1. Missing Package Structure Files
**Problem**: The `commands` directory was missing required Python package files.

**Fix**: Created missing files:
- `src/singlefile_archiver/commands/__init__.py` - Makes directory a Python package
- `src/singlefile_archiver/commands/__main__.py` - Enables module execution

### 2. Package Not Installed
**Problem**: Python couldn't find the `singlefile_archiver` module because it wasn't installed.

**Fix**: Installed the package in development mode:
```bash
pip install -e .
```

This allows the package to be imported from anywhere while still being editable.

## How to Use Now

### Method 1: Direct Module Execution (Recommended)
```bash
FF_BATCH_PROCESSING=true python -m singlefile_archiver.commands.optimize /path/to/archive --dry-run
```

### Method 2: Convenience Script
```bash
python run_optimize.py /path/to/archive --dry-run
```

### Method 3: CLI Script (if available)
```bash
# First ensure feature flag is set
export FF_BATCH_PROCESSING=true
singlefile-archiver optimize /path/to/archive --dry-run
```

## Verification
The fix was tested with a real archive directory containing 3,251 HTML files. The command successfully:
- Scanned all files
- Identified optimization opportunities
- Detected naming conflicts
- Displayed preview table
- Respected the `--dry-run` flag
- Honored the `FF_BATCH_PROCESSING` feature flag

## Feature Flags
Remember to enable batch processing with the feature flag:
```bash
export FF_BATCH_PROCESSING=true
```

Or set it inline with the command as shown in the examples above.