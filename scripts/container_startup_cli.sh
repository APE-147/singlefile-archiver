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

# Check if CLI source is available and use Python directly
if [ -d "/data/scripts/src" ] && [ -f "/data/scripts/src/singlefile_archiver/cli.py" ]; then
    echo "✅ SingleFile Archiver source available"
    CLI_CMD="python -m singlefile_archiver.cli"
    export PYTHONPATH="/data/scripts/src:$PYTHONPATH"
    cd /data/scripts
else
    echo "❌ SingleFile Archiver source not found"
    echo "Expected at: /data/scripts/src/singlefile_archiver/"
    exit 1
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
echo "Command: $CLI_CMD monitor start --watch /data/incoming --archive /data/archive"
echo "Press Ctrl+C to stop (or send SIGTERM to container)"
echo "============================================"
echo ""

# Start the CLI monitor in the background and capture its PID
$CLI_CMD monitor start --watch /data/incoming --archive /data/archive &
MONITOR_PID=$!

# Wait for the background process
wait $MONITOR_PID
