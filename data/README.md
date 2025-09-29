# SingleFile Archiver Data Directory

This directory contains all the data and configuration files for the SingleFile Archiver project.

## Directory Structure

- **`incoming/`** - Files to be monitored and processed
  - Place HTML files with timestamp patterns here
  - Files containing "X 上的" will be automatically processed
  - Files are moved to `archive/` after processing

- **`archive/`** - Processed and archived files  
  - All successfully processed files are stored here
  - Organized by processing date and source

- **`temp/`** - Temporary files during processing
  - Used for intermediate processing steps
  - Automatically cleaned up after operations

- **`logs/`** - Application logs
  - CLI operation logs
  - File processing logs
  - Error and debug information

## Usage

### For File Monitoring
1. Place HTML files in `incoming/` directory
2. Run `singlefile-archiver monitor start` to start monitoring
3. Processed files will appear in `archive/` directory

### For URL Archiving  
1. Place CSV files with URLs in the project root
2. Run `singlefile-archiver archive urls your-file.csv`
3. Archived pages will be saved to `archive/` directory

## Configuration

The system automatically creates and manages these directories. Default paths can be overridden in the configuration file:

```json
{
  "monitor_watch_dir": "${SINGLEFILE_INCOMING_DIR:-/path/to/incoming}",
  "monitor_archive_dir": "${SINGLEFILE_ARCHIVE_DIR:-/path/to/archive}",
  "archive_output_dir": "${SINGLEFILE_ARCHIVE_DIR:-/path/to/archive}"
}
```

## Docker Integration

When using Docker, these directories are mounted as:
- External incoming directory → `/data/incoming` (inside container)
- External archive directory → `/data/archive` (inside container)  
- `./data/logs` → `/app/logs` (inside container)

This allows the containerized services to process files using the same local directory structure.
