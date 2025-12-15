#!/bin/bash
# =============================================================
# Spider News Now - 1Panel Deployment Script
# =============================================================
# Usage:
#   1. First time setup: ./scripts/deploy.sh init
#   2. Update deployment: ./scripts/deploy.sh update
#   3. View logs: ./scripts/deploy.sh logs
#   4. Stop services: ./scripts/deploy.sh stop
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="${DEPLOY_PATH:-/opt/app/spider_news_now}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Initialize deployment directory
init() {
    log_info "Initializing deployment directory: $DEPLOY_DIR"

    # Create directory
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown -R $(whoami):$(whoami) "$DEPLOY_DIR"

    # Copy production files
    cp "$PROJECT_DIR/docker-compose.prod.yml" "$DEPLOY_DIR/docker-compose.prod.yml"
    cp "$PROJECT_DIR/.env.example" "$DEPLOY_DIR/.env.example"

    # Create .env if not exists
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
        log_warn "Created .env file from template. Please edit $DEPLOY_DIR/.env with your values!"
    fi

    # Create logs directory
    mkdir -p "$DEPLOY_DIR/logs"

    # Create RustFS data directory with correct permissions
    mkdir -p "$DEPLOY_DIR/rustfs_data"
    sudo chown -R 10001:10001 "$DEPLOY_DIR/rustfs_data"

    log_info "Initialization complete!"
    log_info "Next steps:"
    echo "  1. Edit $DEPLOY_DIR/.env with your configuration"
    echo "  2. Run: ./scripts/deploy.sh start"
}

# Login to GitHub Container Registry
ghcr_login() {
    if [ -z "$GITHUB_TOKEN" ]; then
        log_error "GITHUB_TOKEN environment variable is required for GHCR login"
        log_info "Set it with: export GITHUB_TOKEN=your_token"
        exit 1
    fi

    echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
    log_info "Logged in to GitHub Container Registry"
}

# Pull latest images
pull() {
    log_info "Pulling latest images..."
    cd "$DEPLOY_DIR"

    # Source environment
    source .env

    docker pull ghcr.io/${GITHUB_REPOSITORY}/backend:latest
    docker pull ghcr.io/${GITHUB_REPOSITORY}/frontend:latest

    log_info "Images pulled successfully"
}

# Start services
start() {
    log_info "Starting services..."
    cd "$DEPLOY_DIR"

    docker-compose -f docker-compose.prod.yml up -d

    log_info "Services started. Checking health..."
    sleep 30

    docker-compose -f docker-compose.prod.yml ps
}

# Update deployment (pull + restart)
update() {
    log_info "Updating deployment..."

    pull

    cd "$DEPLOY_DIR"
    docker-compose -f docker-compose.prod.yml up -d --force-recreate backend frontend

    # Cleanup old images
    docker image prune -f

    log_info "Update complete!"
}

# Stop services
stop() {
    log_info "Stopping services..."
    cd "$DEPLOY_DIR"
    docker-compose -f docker-compose.prod.yml down
    log_info "Services stopped"
}

# View logs
logs() {
    cd "$DEPLOY_DIR"
    docker-compose -f docker-compose.prod.yml logs -f --tail=100 ${2:-}
}

# Show status
status() {
    cd "$DEPLOY_DIR"
    docker-compose -f docker-compose.prod.yml ps
}

# Health check
health() {
    log_info "Running health checks..."

    # Backend health
    if curl -sf http://localhost:8001/api/v1/health > /dev/null; then
        log_info "Backend: OK"
    else
        log_error "Backend: FAILED"
    fi

    # Frontend health
    if curl -sf http://localhost:8080/health > /dev/null 2>&1 || curl -sf http://localhost:8080 > /dev/null; then
        log_info "Frontend: OK"
    else
        log_error "Frontend: FAILED"
    fi
}

# Backup data
backup() {
    BACKUP_DIR="$DEPLOY_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    log_info "Creating backup in $BACKUP_DIR..."

    cd "$DEPLOY_DIR"

    # Backup MySQL
    docker-compose -f docker-compose.prod.yml exec -T mysql mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --all-databases > "$BACKUP_DIR/mysql.sql"

    # Backup .env
    cp .env "$BACKUP_DIR/.env"

    log_info "Backup complete: $BACKUP_DIR"
}

# Main
case "${1:-help}" in
    init)
        init
        ;;
    pull)
        pull
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    update)
        update
        ;;
    logs)
        logs "$@"
        ;;
    status)
        status
        ;;
    health)
        health
        ;;
    backup)
        backup
        ;;
    ghcr-login)
        ghcr_login
        ;;
    *)
        echo "Spider News Now - Deployment Script"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  init        Initialize deployment directory"
        echo "  start       Start all services"
        echo "  stop        Stop all services"
        echo "  update      Pull latest images and restart"
        echo "  pull        Pull latest images only"
        echo "  logs        View service logs (optionally specify service name)"
        echo "  status      Show service status"
        echo "  health      Run health checks"
        echo "  backup      Create backup of database and config"
        echo "  ghcr-login  Login to GitHub Container Registry"
        ;;
esac
