# Requirements Documentation

**⚠️ MANUAL EDITING ONLY ⚠️**
This file contains the original user requirements and application scenarios. It should only be edited manually and never be modified by automated processes.

**Latest requirements are at the top of this file.**

---

## Latest Update: 2025-10-11

### Project Purpose
SingleFile URL Archiver - A comprehensive web archiving system with batch processing capabilities for creating local HTML archives from web URLs.

### Core Requirements

1. **Web Archiving**
   - Archive web pages as single HTML files using SingleFile technology
   - Support for various URL formats and web page types
   - Preserve complete page content including CSS, JavaScript, and images

2. **Batch Processing**
   - Process multiple URLs in batch operations
   - Support for CSV input files with URL lists
   - Enhanced filename generation with conflict resolution

3. **Docker Integration**
   - Containerized deployment for cross-platform compatibility
   - Live code updates without rebuilding containers
   - Service monitoring and management

4. **File Management**
   - Intelligent filename generation with URL encoding
   - Conflict resolution using numbered suffixes (_001, _002, etc.)
   - Byte-aware filename constraints (150-byte limit)
   - Privacy protection in generated filenames

5. **Monitoring & Logging**
   - File system monitoring for automatic processing
   - Comprehensive logging system
   - Service status monitoring

### Application Scenarios

1. **Research & Documentation**
   - Academic research requiring web page preservation
   - Documentation of web-based resources
   - Creating offline references from online content

2. **Content Archival**
   - Personal web page collection and organization
   - Backup of important web content
   - Long-term preservation of web resources

3. **Batch Operations**
   - Processing lists of URLs from spreadsheets
   - Automated archiving workflows
   - Mass web content preservation

### Technical Constraints

- Maximum filename length: 150 bytes (including .html extension)
- Support for Unicode characters in filenames
- Privacy-conscious URL encoding and sanitization
- Cross-platform compatibility (macOS, Linux, Windows via Docker)

### Quality Requirements

- 100% unique filename generation (no conflicts)
- Robust error handling and recovery
- Performance optimization for large batches
- Comprehensive test coverage
- Clear user feedback and progress indication