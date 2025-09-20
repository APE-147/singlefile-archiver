#!/bin/bash

# Migration script to update existing Docker services to use new CLI framework
# This script helps transition from old scripts to new singlefile-archiver CLI

echo "🚀 SingleFile CLI Migration Script"
echo "=================================="
echo ""

# Get current directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_PATH="../bin/singlefile-archiver"

# Check if CLI is installed
if [ ! -f "$CLI_PATH" ]; then
    echo "❌ SingleFile Archiver CLI not found at: $CLI_PATH"
    echo "Please run: bash scripts/install.sh"
    exit 1
fi

echo "✅ CLI found at: $CLI_PATH"
echo ""

# Update Docker compose file for new CLI
echo "📝 Updating docker-compose.yml..."

# Create backup
cp docker-compose.yml docker-compose.yml.backup
echo "📄 Created backup: docker-compose.yml.backup"

# Update file-monitor service to use new CLI
cat > docker-compose-updated.yml << 'EOF'
services:
  singlefile:
    image: capsulecode/singlefile:latest
    container_name: singlefile-cli
    # 主要脚本存放位置
    volumes:
      - .:/data/scripts
      - ./data/incoming:/data/incoming
      - ./data/archive:/data/archive
    # 开机自动启动，持续运行
    restart: always
    # 保持容器运行 - 覆盖默认入口点
    entrypoint: ["sh", "-c", "while true; do sleep 3600; done"]

  file-monitor:
    build:
      context: .
      dockerfile: Dockerfile.monitor-cli
    container_name: singlefile-monitor-cli
    volumes:
      - .:/data/scripts
      - ./data/incoming:/data/incoming
      - ./data/archive:/data/archive
      - ./logs:/app/logs
      - ../bin:/usr/local/bin
    environment:
      - INCOMING_DIR=/data/incoming
      - ARCHIVE_DIR=/data/archive
      - CHECK_INTERVAL=2
      - PYTHONUNBUFFERED=1
    # 开机自动启动，持续运行
    restart: always
    # 依赖关系 - 确保SingleFile容器已启动
    depends_on:
      - singlefile
    # 健康检查
    healthcheck:
      test: ["CMD", "singlefile-archiver", "info"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF

echo "✅ Updated docker-compose-updated.yml created"
echo ""

# Create new Dockerfile for CLI-based monitoring
echo "📝 Creating new Dockerfile for CLI-based monitoring..."

cat > Dockerfile.monitor-cli << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies (watchdog for file monitoring)
RUN pip install --no-cache-dir watchdog

# Create necessary directories
RUN mkdir -p /app/logs /data/incoming /data/archive /data/scripts

# Copy CLI startup script
COPY container_startup_cli.sh /app/
RUN chmod +x /app/container_startup_cli.sh

# Entry point
CMD ["/app/container_startup_cli.sh"]
EOF

echo "✅ Created Dockerfile.monitor-cli"
echo ""

# Create new container startup script for CLI
echo "📝 Creating CLI-based container startup script..."

cat > container_startup_cli.sh << 'EOF'
#!/bin/bash

# Container startup script for CLI-based File Monitor
# This script initializes and starts the file monitoring service using the new CLI

set -e

echo "============================================"
echo "SingleFile CLI Monitor - Container Startup"
echo "============================================"
echo "Container started at: $(date)"
echo "Working directory: $(pwd)"
echo ""

# Check directories
echo "📁 Checking directories..."
echo "Incoming directory: ${INCOMING_DIR:-/data/incoming}"
echo "Archive directory: ${ARCHIVE_DIR:-/data/archive}"
echo "Scripts directory: /data/scripts"
echo "Logs directory: /app/logs"

# Create directories if they don't exist
mkdir -p "${INCOMING_DIR:-/data/incoming}"
mkdir -p "${ARCHIVE_DIR:-/data/archive}"
mkdir -p /data/scripts
mkdir -p /app/logs

echo "✅ Directories ready"
echo ""

# Display configuration
echo "⚙️ Monitor Configuration:"
echo "- Incoming: ${INCOMING_DIR:-/data/incoming}"
echo "- Archive: ${ARCHIVE_DIR:-/data/archive}"
echo "- Check interval: ${CHECK_INTERVAL:-2} seconds"
echo "- Log level: INFO"
echo ""

# Check if CLI is available
if [ -f "/usr/local/bin/singlefile-archiver" ]; then
    echo "✅ SingleFile Archiver CLI available"
    CLI_CMD="/usr/local/bin/singlefile-archiver"
else
    echo "❌ CLI not found, falling back to legacy script"
    CLI_CMD="python3 /data/scripts/file_monitor.py"
fi

# Function to handle shutdown gracefully
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal..."
    echo "Stopping file monitor gracefully..."
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true
    echo "File monitor stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start the file monitor using CLI
echo "🚀 Starting CLI-based file monitoring service..."
echo "Command: $CLI_CMD monitor start"
echo "Press Ctrl+C to stop (or send SIGTERM to container)"
echo "============================================"
echo ""

# Start the CLI monitor in the background and capture its PID
$CLI_CMD monitor start &
MONITOR_PID=$!

# Wait for the background process
wait $MONITOR_PID
EOF

chmod +x container_startup_cli.sh
echo "✅ Created container_startup_cli.sh"
echo ""

# Update docker management script for CLI
echo "📝 Creating CLI-compatible docker management script..."

cat > docker_management_cli.sh << 'EOF'
#!/bin/bash

# SingleFile Docker Services Management Script (CLI Version)
# This script provides easy management of both SingleFile and CLI-based File Monitor services

cd "$(dirname "$0")"

show_help() {
    echo "SingleFile Docker Services Management (CLI Version)"
    echo "=================================================="
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services (singlefile + cli-monitor)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show status of all services"
    echo "  logs      - Show logs from all services"
    echo "  monitor   - Show file monitor logs only"
    echo "  build     - Build/rebuild the CLI monitor image"
    echo "  clean     - Stop and remove all containers and images"
    echo "  migrate   - Switch to CLI-based monitoring"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start both services with CLI"
    echo "  $0 logs               # Show all logs"
    echo "  $0 monitor            # Show only CLI monitor logs"
    echo "  $0 migrate            # Switch to CLI-based compose file"
    echo ""
}

case "$1" in
    migrate)
        echo "🔄 Migrating to CLI-based monitoring..."
        if [ -f docker-compose-updated.yml ]; then
            mv docker-compose.yml docker-compose-legacy.yml
            mv docker-compose-updated.yml docker-compose.yml
            echo "✅ Migrated to CLI-based docker-compose.yml"
            echo "📄 Legacy compose saved as docker-compose-legacy.yml"
        else
            echo "❌ Updated compose file not found. Run migrate_to_cli.sh first."
            exit 1
        fi
        ;;
    
    start)
        echo "🚀 Starting SingleFile CLI services..."
        docker compose up -d
        echo "✅ CLI services started!"
        echo ""
        echo "Checking status..."
        docker compose ps
        ;;
    
    stop)
        echo "🛑 Stopping SingleFile CLI services..."
        docker compose down
        echo "✅ Services stopped!"
        ;;
    
    restart)
        echo "🔄 Restarting SingleFile CLI services..."
        docker compose down
        docker compose up -d
        echo "✅ CLI services restarted!"
        echo ""
        echo "Checking status..."
        docker compose ps
        ;;
    
    status)
        echo "📊 SingleFile CLI Services Status:"
        echo "================================="
        docker compose ps
        echo ""
        echo "Service Health:"
        echo "---------------"
        docker compose exec file-monitor singlefile-archiver info 2>/dev/null && echo "CLI Monitor: ✅ Running" || echo "CLI Monitor: ❌ Not Running"
        docker compose exec singlefile echo "SingleFile CLI: ✅ Running" 2>/dev/null || echo "SingleFile CLI: ❌ Not Running"
        ;;
    
    logs)
        echo "📋 Showing logs from all CLI services (press Ctrl+C to stop):"
        echo "==========================================================="
        docker compose logs -f
        ;;
    
    monitor)
        echo "👁️ Showing CLI monitor logs (press Ctrl+C to stop):"
        echo "=================================================="
        docker compose logs -f file-monitor
        ;;
    
    build)
        echo "🔨 Building CLI monitor image..."
        docker compose build file-monitor
        echo "✅ CLI build completed!"
        ;;
    
    clean)
        echo "🧹 Cleaning up all containers and images..."
        read -p "Are you sure? This will remove all containers and images. (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down --rmi all --volumes
            echo "✅ Cleanup completed!"
        else
            echo "Cleanup cancelled."
        fi
        ;;
    
    help|--help|-h|"")
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
EOF

chmod +x docker_management_cli.sh
echo "✅ Created docker_management_cli.sh"
echo ""

# Summary
echo "📋 Migration Summary:"
echo "===================="
echo "✅ Created updated docker-compose-updated.yml"
echo "✅ Created Dockerfile.monitor-cli for CLI-based monitoring"
echo "✅ Created container_startup_cli.sh for CLI startup"
echo "✅ Created docker_management_cli.sh for CLI service management"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Review the updated files above"
echo "2. To migrate to CLI-based monitoring:"
echo "   ./docker_management_cli.sh migrate"
echo "3. Build and start CLI services:"
echo "   ./docker_management_cli.sh build"
echo "   ./docker_management_cli.sh start"
echo "4. Check status:"
echo "   ./docker_management_cli.sh status"
echo ""
echo "📄 Original files backed up with .backup extension"
echo "🎉 Migration preparation complete!"