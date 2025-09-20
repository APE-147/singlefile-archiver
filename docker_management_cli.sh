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
