# Technology Stack Fingerprint

## Project Overview
- **Name**: singlefile-archiver
- **Version**: 0.1.0
- **Description**: A comprehensive SingleFile URL archiving system with batch processing, file monitoring, and retry mechanisms
- **License**: MIT

## Core Technology Stack

### Programming Language
- **Python**: 3.8+ (supports 3.8, 3.9, 3.10, 3.11, 3.12)
- **Build System**: Hatchling

### Core Dependencies
```toml
typer[all]>=0.12.0        # CLI framework with rich features
docker>=7.1.0             # Docker container management
watchdog>=4.0.0           # File system monitoring
pydantic>=2.0.0           # Data validation and settings
rich>=13.0.0              # Rich terminal output
python-dotenv>=1.0.0      # Environment variable management
```

### Development Dependencies
```toml
pytest>=8.0.0             # Testing framework
pytest-cov>=4.0.0         # Coverage reporting
black>=24.0.0             # Code formatting
ruff>=0.3.0               # Fast Python linter
mypy>=1.8.0               # Static type checking
```

## Tooling Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/singlefile_archiver --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_filename.py -v
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking
mypy src/singlefile_archiver
```

### Project Management
```bash
# Install in development mode
pip install -e ".[dev]"

# Build package
python -m build

# Install from wheel
pip install dist/singlefile_archiver-*.whl
```

## Docker Infrastructure

### Container Images
- `Dockerfile.all-in-one`: Complete archiving solution
- `Dockerfile.monitor-cli`: File monitoring service
- `Dockerfile.singlefile-python`: Python-based SingleFile wrapper

### Docker Compose
- `docker-compose.yml`: Production configuration
- `docker-compose.example.yml`: Template configuration

### Management Scripts
- `docker_management_cli.sh`: Container lifecycle management
- `container_startup_cli.sh`: Container initialization

## Configuration Management

### Environment Variables
- Configuration via `.env` file
- Template provided in `.env.example`
- Privacy-focused design (no hardcoded paths)

### Key Configuration Areas
- Archive storage paths
- Docker container settings
- Monitoring parameters
- Logging configuration

## Code Quality Configuration

### Black (Code Formatting)
```toml
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
```

### Ruff (Linting)
```toml
target-version = "py38"
line-length = 88
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C901"]
```

### MyPy (Type Checking)
```toml
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Project Structure

```
src/singlefile_archiver/
├── cli.py                    # Main CLI entry point
├── core/
│   └── archive.py           # Core archiving logic
├── services/
│   ├── docker_service.py    # Docker container management
│   └── file_monitor.py      # File system monitoring
└── utils/
    └── paths.py             # Path and filename utilities
```

## Continuous Integration

### Quality Gates
1. **Code Formatting**: Black formatting compliance
2. **Linting**: Ruff checks passing
3. **Type Safety**: MyPy validation
4. **Testing**: Full test suite execution
5. **Coverage**: Minimum coverage thresholds

### Pre-commit Workflow
```bash
# Format, lint, and test in sequence
black src/ tests/ && \
ruff check --fix src/ tests/ && \
mypy src/singlefile_archiver && \
pytest --cov=src/singlefile_archiver
```

## Performance Considerations

### Optimization Areas
- File I/O operations
- Docker container startup time
- Archive processing throughput
- Memory usage during batch operations

### Monitoring Metrics
- Archive processing time per URL
- Container resource utilization
- File system watch responsiveness
- Error rates and retry patterns

## Security Considerations

### Privacy Protection
- No hardcoded personal paths
- Environment-based configuration
- Sanitized logging output
- Safe filename generation

### Container Security
- Non-root user execution
- Minimal base images
- Secure mount points
- Network isolation options