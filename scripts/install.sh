#!/usr/bin/env bash
set -euo pipefail

# SingleFile Archiver Installation Script
# Follows standard patterns with uv/venv fallback and wrapper generation

# Use local project directory instead of external data directory
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="singlefile_archiver"
BIN_NAME="singlefile-archiver"
ORG_REVERSE_DNS="com.singlefile-archiver"
PYTHON_MIN_VERSION="3.8"

# Paths
SCRIPTS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
VENV_DIR=".venv"
BIN_DIR="$SCRIPTS_ROOT/bin"

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_python_version() {
    if ! command -v python3 &> /dev/null; then
        echo_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        echo_error "Python ${PYTHON_MIN_VERSION}+ is required, but found Python ${python_version}"
        exit 1
    fi
    
    echo_info "Python version check passed: ${python_version}"
}

install_with_uv() {
    echo_info "Attempting installation with uv..."
    
    if ! command -v uv &> /dev/null; then
        echo_warn "uv not found, installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source "$HOME/.cargo/env" 2>/dev/null || true
        
        if ! command -v uv &> /dev/null; then
            echo_warn "uv installation failed, falling back to venv"
            return 1
        fi
    fi
    
    # Create virtual environment with uv
    uv venv "${VENV_DIR}" --python python3
    
    # Install package in development mode
    uv pip install -e . --python "${VENV_DIR}/bin/python"
    
    echo_info "Installation with uv successful"
    return 0
}

install_with_venv() {
    echo_info "Installing with venv..."
    
    # Create virtual environment
    python3 -m venv "${VENV_DIR}"
    
    # Activate and install
    source "${VENV_DIR}/bin/activate"
    python -m pip install --upgrade pip
    python -m pip install -e .
    
    echo_info "Installation with venv successful"
}

create_wrapper_script() {
    echo_info "Creating wrapper script..."
    
    mkdir -p "${BIN_DIR}"
    
    local wrapper_script="${BIN_DIR}/${BIN_NAME}"
    
    cat > "${wrapper_script}" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Auto-generated wrapper for singlefile-archiver
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "${SCRIPT_DIR}/../service/webpage/singlefile" ]]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../service/webpage/singlefile" && pwd)"
elif [[ -d "${SCRIPT_DIR}/../service/singlefile" ]]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../service/singlefile" && pwd)"
else
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
VENV_PATH="${PROJECT_ROOT}/.venv"

if [[ ! -d "${VENV_PATH}" ]]; then
    echo "Error: Virtual environment not found at ${VENV_PATH}"
    echo "Please run the installation script first"
    exit 1
fi

# Execute the CLI application
exec "${VENV_PATH}/bin/python" -m singlefile_archiver.cli "$@"
EOF
    
    chmod +x "${wrapper_script}"
    echo_info "Wrapper script created at ${wrapper_script}"
}

create_launch_agent() {
    echo_info "Creating macOS Launch Agent..."
    
    mkdir -p "${LAUNCH_AGENTS_DIR}"
    
    local plist_file="${LAUNCH_AGENTS_DIR}/${ORG_REVERSE_DNS}.plist"
    local template_file="scripts/macos/launchd/${BIN_NAME}.plist.template"
    
    if [[ ! -f "${template_file}" ]]; then
        echo_warn "Launch agent template not found: ${template_file}"
        return 1
    fi
    
    # Replace placeholders in template
    sed -e "s|{{BIN_NAME}}|${BIN_NAME}|g" \
        -e "s|{{BIN_PATH}}|${BIN_DIR}/${BIN_NAME}|g" \
        -e "s|{{PROJECT_DIR}}|${PROJECT_DIR}|g" \
        -e "s|{{ORG_REVERSE_DNS}}|${ORG_REVERSE_DNS}|g" \
        "${template_file}" > "${plist_file}"
    
    echo_info "Launch agent created at ${plist_file}"
    echo_info "To enable autostart, run: ${BIN_NAME} autostart --load"
}

setup_project_directories() {
    echo_info "Setting up project directories..."
    
    mkdir -p "${PROJECT_DIR}"
    mkdir -p "${PROJECT_DIR}/archives"
    mkdir -p "${PROJECT_DIR}/incoming"
    mkdir -p "${PROJECT_DIR}/processed"
    mkdir -p "${PROJECT_DIR}/logs"
    
    echo_info "Project directories created in ${PROJECT_DIR}"
}

main() {
    echo_info "Starting SingleFile Archiver installation..."
    echo_info "Project directory: ${PROJECT_DIR}"
    
    # Check prerequisites
    check_python_version
    
    # Install the package
    if install_with_uv; then
        echo_info "Package installed successfully with uv"
    else
        echo_warn "uv installation failed, trying with venv..."
        install_with_venv
        echo_info "Package installed successfully with venv"
    fi
    
    # Create wrapper script
    create_wrapper_script
    
    # Setup project structure
    setup_project_directories
    
    # Create launch agent (macOS only)
    if [[ "$(uname)" == "Darwin" ]]; then
        create_launch_agent
    else
        echo_info "Skipping launch agent creation (not macOS)"
    fi
    
    echo_info "Installation complete!"
    echo_info ""
    echo_info "Next steps:"
    echo_info "1. Test installation: ${BIN_NAME} info"
    echo_info "2. Run tests: ${BIN_NAME} test all"
    echo_info "3. Check Docker: ${BIN_NAME} docker status"
    echo_info ""
    echo_info "For autostart on macOS:"
    echo_info "  ${BIN_NAME} autostart --load"
}

# Check if running as source or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
