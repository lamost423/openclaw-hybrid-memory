# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## Agent Reach

**安装路径:** `/Users/danielwu/Library/Python/3.14/bin/`

**使用方式:**
```bash
export PATH="$HOME/Library/Python/3.14/bin:$PATH"
agent-reach doctor          # 检查状态
agent-reach read <url>      # 读取任意网页
agent-reach search <query>  # 全网搜索
agent-reach tweet <url>     # 读取推文
agent-reach video <url>     # 读取视频字幕
```

**当前状态: 10/12 渠道可用**

✅ 可用：GitHub, Twitter/X(全功能), YouTube, B站, RSS, 网页, Instagram(公开), Reddit, 小红书(全功能)
⬜ 需配置：LinkedIn MCP, Boss直聘MCP

**代理配置:**
- 协议: SOCKS5 (`socks5h://`)
- 认证: `oqqrvzzx:qvo4zq53k74q`
- 10 个住宅节点全部可用:
  63.141.62.74:6367 | 64.52.31.232:6419 | 9.142.215.131:6296
  64.52.29.151:7338 | 9.142.194.6:6674 | 72.1.181.138:5532
  9.142.198.100:5767 | 130.180.232.125:8563 | 192.53.66.195:6301
  192.46.187.155:6733 (当前使用)
- agent-reach 已配置，Reddit + B站 代理生效

## Mem0 记忆系统

**架构:** FAISS 向量搜索 + Neo4j 图谱 + OpenRouter Gemini

**Python 环境:** `~/.openclaw/venv-py311` (Python 3.11，避免 3.14 死锁问题)

**配置文件:** `scripts/mem0_config.py`

**Bridge CLI (增强版):**
```bash
# 激活虚拟环境后使用
source ~/.openclaw/venv-py311/bin/activate

KMP_DUPLICATE_LIB_OK=TRUE python3 scripts/mem0_bridge_enhanced.py search "查询" --user daniel
KMP_DUPLICATE_LIB_OK=TRUE python3 scripts/mem0_bridge_enhanced.py add "记忆内容" --user daniel
KMP_DUPLICATE_LIB_OK=TRUE python3 scripts/mem0_bridge_enhanced.py list --user daniel
KMP_DUPLICATE_LIB_OK=TRUE python3 scripts/mem0_bridge_enhanced.py export --output MEMORY_BACKUP.md --user daniel
```

**组件:**
- **FAISS:** 本地向量存储，3072 维，路径 `~/.openclaw/mem0/faiss_db`
- **Neo4j:** Docker 容器，`bolt://localhost:7687`，认证 `neo4j/mem0password`
- **LLM:** OpenRouter `google/gemini-3-flash-preview`（事实提取）
- **Embedder:** OpenRouter `google/gemini-embedding-001`（3072 维）
- **API Key:** OpenRouter key 在 `mem0_config.py` 中

**注意事项:**
- ⚠️ **必须使用 Python 3.11 虚拟环境** (`venv-py311`)，Python 3.14 有死锁问题
- 所有 python 命令前需加 `KMP_DUPLICATE_LIB_OK=TRUE`
- 已修复 mem0 bug：`utils.py` 的 `sanitize_relationship_for_cypher` 添加 `"-": "_"`
- 已修复 bridge bug：BM25 索引损坏时自动重建
- Neo4j 容器需保持运行：`docker start neo4j`
- 当前存储：~90 条结构化事实

**Docker 容器:**
- `neo4j` — Neo4j 5 图数据库（端口 7474/7687）
- `xiaohongshu-mcp` — 小红书 MCP 服务（端口 18060）

---

Add whatever helps you do your job. This is your cheat sheet.
