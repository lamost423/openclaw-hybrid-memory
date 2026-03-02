#!/bin/bash
# Self-Memory 快速启动脚本

WORKSPACE="$HOME/.openclaw/workspace"
VENV="$HOME/.openclaw/venv"

# 激活虚拟环境
source "$VENV/bin/activate"

# 检查 Ollama 状态
echo "🔍 Checking Ollama status..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "  ⚠️  Ollama not running, starting..."
    brew services start ollama
    sleep 2
fi

# 检查模型
echo "🔍 Checking embedding model..."
if ! ollama list | grep -q "mxbai-embed-large"; then
    echo "  📥 Pulling mxbai-embed-large model..."
    ollama pull mxbai-embed-large
fi

echo "✅ Self-Memory environment ready!"
echo ""
echo "Available commands:"
echo "  hybrid-search <query>     - Search memories with BM25 + Vector"
echo "  compaction-guard          - Backup critical files"
echo "  compaction-guard --list   - List backups"
echo ""

# 进入工作目录
cd "$WORKSPACE"

# 保持 shell 打开
exec bash
