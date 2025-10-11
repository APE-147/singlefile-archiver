# Docker Live Code Updates Configuration

This document explains how to use the Docker volume mounting configuration for live code updates without rebuilding images.

## Overview

The project is now configured to mount source code directories directly into the Docker container, allowing real-time code changes without requiring image rebuilds. This significantly speeds up development and debugging workflows.

## Configuration Files

### 1. Production Configuration (`docker-compose.yml`)

The main docker-compose.yml uses optimized volume mounts:

```yaml
volumes:
  # Core application source code - live updates
  - "./src:/data/scripts/src"
  # Scripts directory for utilities and helpers
  - "./scripts:/data/scripts/scripts"
  # Configuration files (read-only)
  - "./pyproject.toml:/data/scripts/pyproject.toml:ro"
  - "./.env:/data/scripts/.env:ro"
  # Container startup script (read-only)
  - "./container_startup_cli.sh:/usr/local/bin/container_startup_cli.sh:ro"
  # Data directories
  - "${SINGLEFILE_INCOMING_DIR:-./data/incoming}:/data/incoming"
  - "${SINGLEFILE_ARCHIVE_DIR:-./data/archive}:/data/archive"
  - "./data/logs:/app/logs"
  # Test files for debugging (read-only)
  - "./tests:/data/scripts/tests:ro"
```

### 2. Development Configuration (`docker-compose.dev.yml`)

For development with additional debugging features:

```bash
# Use development configuration
docker-compose -f docker-compose.dev.yml up -d

# Or extend the base configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Usage Instructions

### Starting the Service

```bash
# Standard production setup
docker-compose up -d

# Development setup with debugging features
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f singlefile
```

### Live Code Updates Workflow

1. **Edit Code Locally**: Make changes to any Python file in `src/singlefile_archiver/`
   ```bash
   # Example: Edit a function
   vim src/singlefile_archiver/commands/optimize.py
   ```

2. **Changes Take Effect Immediately**: No rebuild needed
   ```bash
   # Verify your changes are in the container
   docker exec singlefile-cli cat /data/scripts/src/singlefile_archiver/commands/optimize.py
   ```

3. **Test New Functionality**: Run commands directly in container
   ```bash
   # Test the latest code changes
   docker exec singlefile-cli python -c "
   from singlefile_archiver.commands.optimize import your_function
   result = your_function()
   print(result)
   "
   ```

### Container Management

```bash
# Restart service (preserves volume mounts)
docker-compose restart

# Stop service
docker-compose down

# View container status
docker-compose ps

# Access interactive shell
docker exec -it singlefile-cli sh
```

## Benefits

### For Development
- **Instant Updates**: Code changes take effect immediately
- **No Rebuild Time**: Skip the docker build step entirely
- **Live Debugging**: Modify code while container is running
- **Fast Iteration**: Edit-test cycle is dramatically faster

### For Production
- **Version Control**: Container always uses exact local code version
- **Easy Rollback**: Switch git branches to change container code
- **Consistent Environment**: Same container, different code versions
- **Deployment Flexibility**: Update code without image rebuilds

## Technical Details

### Python Path Configuration
- Container sets `PYTHONPATH=/data/scripts/src`
- Modules imported as `from singlefile_archiver.module import function`
- All existing import paths continue to work

### File Permissions
- Source code: Read-write (allows live editing)
- Config files: Read-only (prevents accidental modification)
- Test files: Read-only (prevents test pollution)

### Volume Mount Strategy
- **Granular Mounting**: Only necessary directories mounted
- **Performance Optimized**: Excludes heavy folders (.git, .venv, __pycache__)
- **Security Conscious**: Config files mounted read-only where appropriate

## Troubleshooting

### Issue: Module Import Errors
```bash
# Check Python path
docker exec singlefile-cli python -c "import sys; print(sys.path)"

# Verify mounted directories
docker exec singlefile-cli ls -la /data/scripts/src/
```

### Issue: Changes Not Reflected
```bash
# Verify file timestamps
docker exec singlefile-cli ls -la /data/scripts/src/singlefile_archiver/commands/

# Check if file is actually mounted
docker exec singlefile-cli mount | grep /data/scripts
```

### Issue: Container Won't Start
```bash
# Check container logs
docker-compose logs singlefile

# Verify all mounted paths exist locally
ls -la src/ scripts/ tests/
```

## Examples

### Example 1: Fix a Bug and Test Immediately
```bash
# 1. Edit the problematic function
vim src/singlefile_archiver/commands/optimize.py

# 2. Test the fix without rebuilding
docker exec singlefile-cli python -c "
from singlefile_archiver.commands.optimize import _ensure_unique_filename
result = _ensure_unique_filename('test', {'test'})
print(f'Fixed function result: {result}')
"

# 3. If needed, restart service to reload modules
docker-compose restart
```

### Example 2: Add New Feature and Validate
```bash
# 1. Add new function to a module
echo "def new_feature(): return 'working'" >> src/singlefile_archiver/utils/helpers.py

# 2. Test immediately
docker exec singlefile-cli python -c "
from singlefile_archiver.utils.helpers import new_feature
print(new_feature())
"
```

### Example 3: Switch Code Versions
```bash
# 1. Switch to different git branch
git checkout feature/new-algorithm

# 2. Container automatically uses new code
docker exec singlefile-cli python -c "
# New algorithm is now active
from singlefile_archiver.core.algorithm import process
print('Using new algorithm version')
"

# 3. Switch back if needed
git checkout main
```

## Best Practices

1. **Version Control**: Always commit working changes before switching branches
2. **Testing**: Use the test files mounted in `/data/scripts/tests/` for validation
3. **Logging**: Monitor container logs during development: `docker-compose logs -f`
4. **Backup**: Keep local backups of critical changes before testing
5. **Documentation**: Update function docstrings as you modify code

## Security Considerations

- Config files (.env, pyproject.toml) are mounted read-only
- Container startup script is read-only to prevent tampering
- Source code has write access for development flexibility
- Data directories remain properly isolated

This configuration provides the perfect balance of development speed and production safety.