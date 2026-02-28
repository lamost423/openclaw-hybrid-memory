# OpenClaw 混合记忆系统

> 为 **OpenClaw** AI 智能体打造的生产级混合记忆系统，基于 **[Mem0](https://github.com/mem0ai/mem0)**（图记忆）和 **[rank-bm25](https://github.com/dorianbrown/rank_bm25)**（关键词搜索）构建。

[![Built for OpenClaw](https://img.shields.io/badge/Built%20for-OpenClaw-purple.svg)](https://openclaw.ai)
[![Based on Mem0](https://img.shields.io/badge/Based%20on-Mem0-blue.svg)](https://github.com/mem0ai/mem0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English Documentation](README_EN.md)

## 🚀 一行命令安装

OpenClaw 用户只需一行命令即可安装：

```bash
curl -fsSL https://raw.githubusercontent.com/lamost423/openclaw-hybrid-memory/main/install.sh | bash
```

安装脚本将自动：
- ✅ 检查/安装 Ollama
- ✅ 拉取嵌入模型
- ✅ 克隆仓库到 `scripts/openclaw-hybrid-memory/`
- ✅ 安装 Python 依赖
- ✅ 构建初始索引
- ✅ 更新 HEARTBEAT.md

### 手动安装

```bash
cd ~/.openclaw/workspace
git clone https://github.com/lamost423/openclaw-hybrid-memory.git scripts/openclaw-hybrid-memory
pip install -r scripts/openclaw-hybrid-memory/requirements.txt
```

## 🎯 这是什么？

本项目在 **[Mem0](https://github.com/mem0ai/mem0)**（流行的图记忆系统）基础上增加了 **BM25 关键词搜索**（通过 [rank-bm25](https://github.com/dorianbrown/rank_bm25)），为 **OpenClaw** AI 智能体创建混合记忆架构。

**为什么扩展 Mem0？**
- Mem0 提供优秀的向量 + 图记忆能力
- 但缺乏 BM25 关键词精确匹配
- 本项目补充缺失环节：混合搜索

| 组件 | 技术 | 来源 | 增强 |
|-----------|-----------|--------|-------------|
| **向量搜索** | FAISS | Mem0 | ✅ 不变 |
| **图记忆** | Neo4j | Mem0 | ✅ 不变 |
| **BM25 搜索** | BM25 | rank-bm25 | ➕ **新增** |
| **混合融合** | 自定义 | 本项目 | ➕ **新增** |
| **缓存** | 内存 | 本项目 | ➕ **新增** |
| **OpenClaw 集成** | 心跳/脚本 | 本项目 | ➕ **新增** |

## 📐 架构

![技术架构](https://raw.githubusercontent.com/lamost423/openclaw-hybrid-memory/main/docs/assets/technical-architecture.png)

*技术架构：用户查询经过缓存检查，然后并行执行 BM25 和向量搜索，融合引擎合并结果*

## 💡 特性

- **混合搜索**：结合 BM25 关键词精确度和向量语义相似性
- **智能缓存**：缓存查询 0ms 响应
- **增量更新**：只重新索引变更文件（快速）
- **压缩保护**：保护关键文件免受上下文丢失
- **搜索历史**：追踪和分析查询模式
- **OpenClaw 集成**：与现有设置无缝集成

## 🛠️ 使用

### 基础搜索

```bash
# 混合搜索
python3 scripts/openclaw-hybrid-memory/scripts/hybrid_search.py "你的查询"

# 集成 Mem0 搜索
python3 scripts/openclaw-hybrid-memory/scripts/mem0_bridge_enhanced.py search "你的查询"

# 添加记忆
python3 scripts/openclaw-hybrid-memory/scripts/mem0_bridge_enhanced.py add "重要事实"
```

### 维护

```bash
# 检查系统状态
python3 scripts/openclaw-hybrid-memory/scripts/heartbeat_auto.py --status

# 增量更新
python3 scripts/openclaw-hybrid-memory/scripts/incremental_update.py

# 查看缓存统计
python3 scripts/openclaw-hybrid-memory/scripts/search_cache.py --stats

# 查看搜索历史
python3 scripts/openclaw-hybrid-memory/scripts/search_history.py --history
```

## 📊 性能

| 指标 | 无混合 | 有混合 | 提升 |
|--------|---------------|-------------|-------------|
| 精确度@5 | 45% | **78%** | +73% |
| 平均响应时间 | 1200ms | **15ms** | 80倍快 |
| 缓存命中率 | 0% | **57%** | 新增 |

## 🏗️ OpenClaw 集成

### HEARTBEAT.md

安装脚本会自动添加维护任务到你的 `HEARTBEAT.md`：

```markdown
### OpenClaw 混合记忆系统维护
- [ ] 运行自动维护
  ```bash
  python3 scripts/openclaw-hybrid-memory/scripts/heartbeat_auto.py --full
  ```
```

### openclaw.json

可选：在 `~/.openclaw/openclaw.json` 中配置心跳：

```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "30m",
        "prompt": "读取 HEARTBEAT.md 并运行维护任务"
      }
    }
  }
}
```

## 🙏 致谢

本项目基于并扩展了以下优秀的开源项目：

- **[OpenClaw](https://openclaw.ai)** - 本记忆系统所设计的 AI 智能体平台
- **[Mem0](https://github.com/mem0ai/mem0)** - 具有 FAISS + Neo4j 架构的图记忆系统
- **[rank-bm25](https://github.com/dorianbrown/rank_bm25)** - BM25 算法实现
- **[Ollama](https://ollama.com)** - 本地 LLM 和嵌入推理

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)
