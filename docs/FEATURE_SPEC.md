# Feature Specification: Filename Optimization

## Problem Statement

The current SingleFile archiver generates filenames that can become unwieldy and inconsistent:

1. **Excessive Length**: Page titles can be extremely long, resulting in filenames that exceed filesystem limits or become difficult to manage
2. **Emoji Pollution**: Modern web content often includes emoji characters in titles, which can cause issues with:
   - Cross-platform compatibility
   - Terminal display
   - File system restrictions
   - Backup and sync tools
3. **Inconsistent Naming**: Existing archived files don't follow a standardized naming convention

## Objectives

### Primary Goals
1. **Length Control**: Implement intelligent filename length management with graceful truncation
2. **Character Sanitization**: Remove emoji and special characters while preserving readability
3. **Batch Processing**: Provide tooling to apply new naming rules to existing archived files
4. **Backward Compatibility**: Ensure existing functionality remains unaffected

### Non-Goals
- Changing the core archiving workflow
- Modifying the SingleFile container behavior
- Altering the file monitoring system logic
- Breaking existing CLI interfaces

## Requirements

### 1. Filename Length Control
**User Story**: As a user, I want archived filenames to be reasonably short so they don't cause filesystem issues or display problems.

**Acceptance Criteria**:
- Maximum base filename length of 120 characters (excluding extension)
- Intelligent truncation that preserves meaningful content
- Use ellipsis ("...") to indicate truncation
- Maintain URL encoding compatibility

**Examples**:
```
Input:  "This is an extremely long article title that goes on and on about various topics and eventually becomes too long for practical filesystem use"
Output: "This is an extremely long article title that goes on and on about various topics and eventually becomes too..."

Input:  "Short title"
Output: "Short title"
```

### 2. Emoji and Special Character Removal
**User Story**: As a user, I want archived filenames to be clean and compatible across all platforms and tools.

**Acceptance Criteria**:
- Remove all emoji characters (Unicode categories Emoji_Presentation, Extended_Pictographic)
- Remove or replace problematic Unicode characters
- Preserve basic punctuation that adds meaning
- Maintain readability of the filename

**Examples**:
```
Input:  "Amazing Product Review ⭐️⭐️⭐️⭐️⭐️ Must Read! 🔥"
Output: "Amazing Product Review Must Read"

Input:  "Weather Update: ☀️ Sunny with 🌡️ 25°C"
Output: "Weather Update Sunny with 25°C"

Input:  "GitHub: Issue #123 - Fix bug 🐛"
Output: "GitHub Issue 123 - Fix bug"
```

### 3. Batch Processing for Existing Files
**User Story**: As a user, I want to apply the new naming rules to my existing archived files so they follow a consistent pattern.

**Acceptance Criteria**:
- Scan archive directory for existing files
- Apply new naming rules to generate candidate new names
- Preview changes before applying them
- Handle filename conflicts gracefully
- Preserve file modification times and metadata
- Provide dry-run mode for safety

**Workflow**:
```bash
# Preview changes
singlefile-archiver optimize-filenames --dry-run /path/to/archives

# Apply changes with confirmation
singlefile-archiver optimize-filenames --interactive /path/to/archives

# Batch apply (use with caution)
singlefile-archiver optimize-filenames --force /path/to/archives
```

## Technical Design

### Core Functions

#### `optimize_filename(title: str, max_length: int = 120) -> str`
- Remove emoji and special characters
- Truncate intelligently at word boundaries
- Add ellipsis for truncated names
- Ensure filesystem safety

#### `remove_emoji(text: str) -> str`
- Use Unicode character categories for emoji detection
- Remove emoji presentation characters
- Handle composite emoji sequences
- Preserve meaningful Unicode characters

#### `batch_rename_files(directory: Path, dry_run: bool = True) -> List[RenameOperation]`
- Scan directory for archive files
- Generate optimized names for each file
- Detect and resolve naming conflicts
- Return list of proposed operations

### Integration Points

#### Modified Files
- `src/singlefile_archiver/utils/paths.py`: Add new utility functions
- `src/singlefile_archiver/services/docker_service.py`: Update filename generation
- `src/singlefile_archiver/cli.py`: Add new batch command

#### New Files
- `src/singlefile_archiver/commands/optimize.py`: Batch processing command
- `tests/test_filename_optimization.py`: Comprehensive test suite

## Constraints

### Technical Constraints
- Must maintain existing URL encoding functionality
- Cannot break Docker container integration
- Must work across Python 3.8+ versions
- Should not significantly impact performance

### Business Constraints
- Zero downtime deployment required
- Backward compatibility mandatory
- User data safety paramount
- Incremental rollout capability needed

## Risk Assessment

### High Risk
- **Data Loss**: Batch renaming operations could overwrite files
  - *Mitigation*: Comprehensive dry-run mode, backup recommendations
- **Breaking Changes**: Filename format changes could break user workflows
  - *Mitigation*: Feature flags, gradual rollout

### Medium Risk
- **Performance Impact**: Unicode processing could slow filename generation
  - *Mitigation*: Efficient algorithms, performance testing
- **Character Encoding Issues**: Cross-platform filename compatibility
  - *Mitigation*: Extensive testing on different filesystems

### Low Risk
- **User Adoption**: Users might not want the new naming convention
  - *Mitigation*: Make optimization optional, clear documentation

## Validation Strategy

### Acceptance Tests
```gherkin
Feature: Filename Length Control
  Scenario: Long title truncation
    Given a page title longer than 120 characters
    When I generate an archive filename
    Then the filename should be truncated to 120 characters
    And it should end with "..."
    And it should break at a word boundary when possible

Feature: Emoji Removal
  Scenario: Title with emoji characters
    Given a page title containing emoji
    When I generate an archive filename
    Then all emoji characters should be removed
    And the filename should remain readable
    And no invalid filesystem characters should remain

Feature: Batch Processing
  Scenario: Dry run preview
    Given a directory with existing archive files
    When I run optimize-filenames with --dry-run
    Then I should see a preview of all proposed changes
    And no files should be modified
    And conflicts should be identified
```

### Performance Targets
- Filename optimization: <10ms per operation
- Batch processing: <1s per 100 files
- Memory usage: <50MB for 10,000 file operations

## Observability

### Metrics
- `filename_optimization_duration_ms`: Time to optimize a single filename
- `batch_operation_file_count`: Number of files processed in batch operations
- `filename_conflicts_detected`: Number of naming conflicts during batch processing
- `emoji_characters_removed`: Count of emoji characters stripped from filenames

### Logging
- INFO: Successful filename optimizations
- WARN: Potential conflicts or edge cases
- ERROR: Failed operations or validation errors
- DEBUG: Detailed character processing information

### Alerts
- High error rate in filename processing
- Unusual number of conflicts in batch operations
- Performance degradation in optimization functions

## Feature Flags

### `FF_FILENAME_OPTIMIZATION`
- **Default**: `false`
- **Purpose**: Enable new filename optimization functions
- **Scope**: Individual filename generation operations

### `FF_BATCH_PROCESSING`
- **Default**: `false`
- **Purpose**: Enable batch file renaming functionality
- **Scope**: CLI batch commands

### Kill Switch
Emergency disable via environment variable `DISABLE_FILENAME_OPTIMIZATION=true`

## Rollback Strategy

### Immediate Rollback
1. Set kill switch environment variable
2. Restart affected services
3. Revert to previous container image if needed

### Data Recovery
1. Batch operations should create manifest of changes
2. Provide rollback command to reverse batch operations
3. Maintain original filename mappings in operation logs

### Rollback Testing
- Regular verification of rollback procedures
- Automated rollback capability testing
- Recovery time objective: <5 minutes

## Security Considerations

### Input Validation
- Sanitize all filename inputs
- Prevent directory traversal attacks
- Validate Unicode character sequences

### File System Safety
- Ensure generated filenames are valid across platforms
- Prevent filename collision attacks
- Maintain proper file permissions

### Privacy Protection
- No logging of potentially sensitive title content
- Secure handling of file operation manifests
- Privacy-compliant batch operation logs

## Internationalization

### Unicode Handling
- Proper Unicode normalization (NFC)
- Language-aware truncation when possible
- Preservation of essential diacritics and characters

### Character Set Support
- Full UTF-8 support
- Platform-specific filename restrictions
- Graceful degradation for unsupported characters