#!/bin/bash
# =============================================================
# Spider News Now - 部署与回滚脚本
# =============================================================

set -e

PROJECT_DIR="/opt/app/spider_news_now"
BACKUP_DIR="/opt/app/backups"
COMPOSE_FILE="docker-compose.prod.yml"
MAX_BACKUPS=5

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 获取当前版本
get_current_version() {
    cd $PROJECT_DIR
    git rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

# 清理旧镜像和容器
cleanup() {
    log_info "清理旧镜像和容器..."

    # 清理停止的容器
    docker container prune -f 2>/dev/null || true

    # 清理悬空镜像 (dangling images)
    docker image prune -f 2>/dev/null || true

    # 清理未使用的镜像（保留正在使用的）
    docker image prune -a -f --filter "until=24h" 2>/dev/null || true

    # 清理构建缓存
    docker builder prune -f --keep-storage 2GB 2>/dev/null || true

    # 显示磁盘使用情况
    log_info "当前 Docker 磁盘使用:"
    docker system df
}

# 备份当前版本
backup() {
    local version=$(get_current_version)
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/${timestamp}_${version}"

    mkdir -p "$backup_path"

    log_info "备份当前版本: $version -> $backup_path"

    # 保存当前镜像
    docker save spider_news_now-backend:latest -o "$backup_path/backend.tar" 2>/dev/null || true
    docker save spider_news_now-frontend:latest -o "$backup_path/frontend.tar" 2>/dev/null || true

    # 保存版本信息
    echo "$version" > "$backup_path/version.txt"
    echo "$(date)" >> "$backup_path/version.txt"

    # 清理旧备份，只保留最近 N 个
    cd "$BACKUP_DIR"
    ls -dt */ 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -rf 2>/dev/null || true

    log_info "备份完成"
}

# 部署新版本
deploy() {
    cd $PROJECT_DIR

    log_info "开始部署..."

    # 备份当前版本
    backup

    # 拉取最新代码
    log_info "拉取最新代码..."
    git fetch origin main
    git reset --hard origin/main

    # 构建新镜像
    log_info "构建镜像..."
    docker compose -f $COMPOSE_FILE build backend frontend

    # 停止旧容器
    log_info "停止旧容器..."
    docker compose -f $COMPOSE_FILE stop backend frontend
    docker compose -f $COMPOSE_FILE rm -f backend frontend

    # 启动新服务
    log_info "启动服务..."
    docker compose -f $COMPOSE_FILE up -d backend frontend

    # 健康检查
    log_info "等待服务启动..."
    sleep 30

    if curl -sf http://127.0.0.1:8000/api/v1/health > /dev/null; then
        log_info "部署成功！版本: $(get_current_version)"

        # 清理旧镜像和容器
        cleanup
    else
        log_error "部署失败！自动回滚..."
        rollback
        exit 1
    fi
}

# 回滚到上一个版本
rollback() {
    local backup_path=$(ls -dt ${BACKUP_DIR}/*/ 2>/dev/null | head -1)

    if [ -z "$backup_path" ]; then
        log_error "没有可用的备份"
        exit 1
    fi

    local version=$(cat "$backup_path/version.txt" | head -1)
    log_info "回滚到版本: $version"

    cd $PROJECT_DIR

    # 停止当前服务
    docker compose -f $COMPOSE_FILE stop backend frontend
    docker compose -f $COMPOSE_FILE rm -f backend frontend

    # 恢复镜像
    if [ -f "$backup_path/backend.tar" ]; then
        log_info "恢复 backend 镜像..."
        docker load -i "$backup_path/backend.tar"
    fi

    if [ -f "$backup_path/frontend.tar" ]; then
        log_info "恢复 frontend 镜像..."
        docker load -i "$backup_path/frontend.tar"
    fi

    # 重启服务
    docker compose -f $COMPOSE_FILE up -d backend frontend

    log_info "回滚完成"
}

# 列出可用备份
list_backups() {
    log_info "可用备份:"
    ls -lh ${BACKUP_DIR}/ 2>/dev/null || echo "无备份"
}

# 查看状态
status() {
    log_info "当前版本: $(get_current_version)"
    echo ""
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep news_scraper
}

# 主命令
case "${1:-help}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    backup)
        backup
        ;;
    cleanup)
        cleanup
        ;;
    list)
        list_backups
        ;;
    status)
        status
        ;;
    *)
        echo "用法: $0 <命令>"
        echo ""
        echo "命令:"
        echo "  deploy    部署最新版本（自动备份+清理）"
        echo "  rollback  回滚到上一个版本"
        echo "  backup    手动备份当前版本"
        echo "  cleanup   手动清理旧镜像和容器"
        echo "  list      列出可用备份"
        echo "  status    查看当前状态"
        ;;
esac
