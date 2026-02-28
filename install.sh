#!/bin/bash
# One-Click Install Script for OpenClaw Hybrid Memory
# Usage: curl -fsSL https://raw.githubusercontent.com/lamost423/openclaw-hybrid-memory/main/install.sh | bash

set -e

echo "🚀 Installing OpenClaw Hybrid Memory..."
echo ""

# Check if running in OpenClaw workspace
if [ -z "$OPENCLAW_WORKSPACE" ]; then
    if [ -d "$HOME/.openclaw/workspace" ]; then
        OPENCLAW_WORKSPACE="$HOME/.openclaw/workspace"
    else
        echo "❌ Error: OpenClaw workspace not found!"
        echo "Please ensure OpenClaw is installed and initialized."
        exit 1
    fi
fi

echo "📁 OpenClaw workspace: $OPENCLAW_WORKSPACE"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "▶️  Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Pull embedding model
echo "📥 Pulling embedding model (mxbai-embed-large)..."
ollama pull mxbai-embed-large

# Clone repository
echo "📥 Cloning OpenClaw Hybrid Memory..."
cd "$OPENCLAW_WORKSPACE"
if [ -d "scripts/openclaw-hybrid-memory" ]; then
    echo "⚠️  Directory exists, updating..."
    cd scripts/openclaw-hybrid-memory
    git pull
else
    git clone https://github.com/lamost423/openclaw-hybrid-memory.git scripts/openclaw-hybrid-memory
fi

# Install Python dependencies
echo "📥 Installing Python dependencies..."
if [ -f "$OPENCLAW_WORKSPACE/.venv/bin/pip" ] || [ -f "$OPENCLAW_WORKSPACE/venv/bin/pip" ]; then
    # Use existing venv
    if [ -f "$OPENCLAW_WORKSPACE/.venv/bin/pip" ]; then
        "$OPENCLAW_WORKSPACE/.venv/bin/pip" install -r scripts/openclaw-hybrid-memory/requirements.txt
    else
        "$OPENCLAW_WORKSPACE/venv/bin/pip" install -r scripts/openclaw-hybrid-memory/requirements.txt
    fi
else
    # Create new venv
    python3 -m venv "$OPENCLAW_WORKSPACE/.venv"
    "$OPENCLAW_WORKSPACE/.venv/bin/pip" install -r scripts/openclaw-hybrid-memory/requirements.txt
fi

# Build initial index
echo "🔨 Building initial search index..."
if [ -d "$OPENCLAW_WORKSPACE/memory" ]; then
    cd scripts/openclaw-hybrid-memory
    if [ -f "$OPENCLAW_WORKSPACE/.venv/bin/python" ]; then
        "$OPENCLAW_WORKSPACE/.venv/bin/python" scripts/build_index.py --source-dir "$OPENCLAW_WORKSPACE/memory"
    else
        "$OPENCLAW_WORKSPACE/venv/bin/python" scripts/build_index.py --source-dir "$OPENCLAW_WORKSPACE/memory"
    fi
else
    echo "⚠️  No memory/ directory found, skipping index build"
fi

# Add to HEARTBEAT.md
echo "📝 Updating HEARTBEAT.md..."
HEARTBEAT_FILE="$OPENCLAW_WORKSPACE/HEARTBEAT.md"
if [ -f "$HEARTBEAT_FILE" ]; then
    if ! grep -q "openclaw-hybrid-memory" "$HEARTBEAT_FILE"; then
        cat >> "$HEARTBEAT_FILE" << 'EOF'

### OpenClaw Hybrid Memory Maintenance
- [ ] Run automated maintenance
  ```bash
  python3 scripts/openclaw-hybrid-memory/scripts/heartbeat_auto.py --full
  ```
EOF
    fi
else
    cat > "$HEARTBEAT_FILE" << 'EOF'
# Heartbeat Checklist

### OpenClaw Hybrid Memory Maintenance
- [ ] Run automated maintenance
  ```bash
  python3 scripts/openclaw-hybrid-memory/scripts/heartbeat_auto.py --full
  ```
EOF
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Quick Start:"
echo "   cd $OPENCLAW_WORKSPACE"
echo "   python3 scripts/openclaw-hybrid-memory/scripts/hybrid_search.py \"your query\""
echo ""
echo "📚 Documentation: https://github.com/lamost423/openclaw-hybrid-memory"
echo ""
