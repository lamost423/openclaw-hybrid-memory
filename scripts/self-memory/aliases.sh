#!/bin/bash
# Self-Memory 命令别名

WORKSPACE="$HOME/.openclaw/workspace"
VENV="$HOME/.openclaw/venv"
SCRIPTS="$WORKSPACE/scripts/self-memory"

# 激活虚拟环境
source "$VENV/bin/activate"

# 执行混合搜索
hybrid-search() {
    if [ -z "$1" ]; then
        echo "Usage: hybrid-search <query>"
        return 1
    fi
    python3 "$SCRIPTS/hybrid_search.py" "$@"
}

# 执行 Compaction Guard
compaction-guard() {
    python3 "$SCRIPTS/compaction_guard.py" "$@"
}

# 列出备份
list-backups() {
    python3 "$SCRIPTS/compaction_guard.py" --list "$@"
}

# 恢复备份
restore-backup() {
    if [ -z "$1" ]; then
        echo "Usage: restore-backup <path> [timestamp]"
        return 1
    fi
    if [ -n "$2" ]; then
        python3 "$SCRIPTS/compaction_guard.py" --restore "$1" --timestamp "$2"
    else
        python3 "$SCRIPTS/compaction_guard.py" --restore "$1"
    fi
}

# 显示帮助
self-memory-help() {
    echo "Self-Memory Commands:"
    echo ""
    echo "  hybrid-search <query>           - Search with BM25 + Vector fusion"
    echo "  compaction-guard                - Check and backup critical files"
    echo "  compaction-guard --force        - Force backup (ignore cooldown)"
    echo "  list-backups [path]             - List backup files"
    echo "  restore-backup <path> [ts]      - Restore from backup"
    echo ""
    echo "Examples:"
    echo "  hybrid-search '100w目标'"
    echo "  hybrid-search '宠物品牌' --top-k 10"
    echo "  compaction-guard"
    echo "  list-backups"
    echo "  restore-backup SESSION-STATE.md"
}

# 自动提示
echo "Self-Memory loaded! Type 'self-memory-help' for commands."
