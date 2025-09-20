# Changelog

All notable changes to the SingleFile Archiver project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-08-24

### Added
- Initial release of SingleFile Archiver CLI
- URL archiving from CSV files using SingleFile Docker container
- File monitoring with configurable patterns and intervals
- Failed URL tracking and retry mechanisms
- Docker service management (start, stop, status, test)
- Batch URL processing with configurable batch sizes
- macOS Launch Agent integration for autostart
- Comprehensive test suite with multiple test scenarios
- Configuration management with JSON persistence
- Atomic state management for reliability
- Rich terminal output with tables and progress indicators
- CSV file processing and validation
- Project directory structure management
- Installation script with uv/venv fallback
- Wrapper script generation for easy CLI access

### Features
- **Archive Commands**: Single URL and batch CSV archiving
- **Monitor Commands**: Continuous and one-time file monitoring
- **Retry Commands**: Failed URL retry with configurable attempts
- **Docker Commands**: Complete Docker service management
- **Test Commands**: Comprehensive testing framework
- **Utility Commands**: Info, state management, and autostart

### Technical Details
- Built with Typer CLI framework
- Uses Pydantic for configuration validation
- Rich library for enhanced terminal output
- Docker integration for SingleFile container
- Cross-platform support with macOS-specific features
- Follows standard project layout patterns
- Comprehensive error handling and logging