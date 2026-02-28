# OpenClaw Hybrid Memory / OpenClaw 混合记忆系统

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

> A production-ready hybrid memory system for **OpenClaw** AI agents, built on top of **[Mem0](https://github.com/mem0ai/mem0)** (graph memory) and **[rank-bm25](https://github.com/dorianbrown/rank_bm25)** (keyword search).

[![Built for OpenClaw](https://img.shields.io/badge/Built%20for-OpenClaw-purple.svg)](https://openclaw.ai)
[![Based on Mem0](https://img.shields.io/badge/Based%20on-Mem0-blue.svg)](https://github.com/mem0ai/mem0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### 🚀 One-Line Installation

```bash
curl -fsSL https://raw.githubusercontent.com/lamost423/openclaw-hybrid-memory/main/install.sh | bash
```

### What is This?

This project extends **Mem0** with **BM25 keyword search** to create a hybrid memory architecture for OpenClaw AI agents.

**Why extend Mem0?**
- Mem0 provides excellent vector + graph capabilities
- But it lacks BM25 keyword precision for exact matches
- This project adds the missing piece: hybrid search

### Features

- **Hybrid Search**: BM25 (30%) + Vector (70%) fusion
- **Smart Caching**: 0ms response for repeated queries
- **Incremental Updates**: Only re-index changed files
- **OpenClaw Integration**: Works with existing Mem0 setup

### Quick Start

```bash
# Search
python3 scripts/openclaw-hybrid-memory/scripts/hybrid_search.py "your query"

# Check status
python3 scripts/openclaw-hybrid-memory/scripts/heartbeat_auto.py --status
```

---

<a name="中文"></a>
## 中文

> 为 **OpenClaw** AI 智能体打造的生产级混合记忆系统，基于 **[Mem0](https://github.com/mem0ai/mem0)**（图记忆）和 **[rank-bm25](https://github.com/dorianbrown/rank_bm25)**（关键词搜索）构建。

### 🚀 一行命令安装

```bash
curl -fsSL https://raw.githubusercontent.com/lamost423/openclaw-hybrid-memory/main/install.sh | bash
```

### 这是什么？

本项目在 **Mem0** 基础上增加了 **BM25 关键词搜索**，为 OpenClaw AI 智能体创建混合记忆架构。

**为什么扩展 Mem0？**
- Mem0 提供优秀的向量 + 图记忆能力
- 但缺乏 BM25 关键词精确匹配
- 本项目补充缺失环节：混合搜索

### 特性

- **混合搜索**：BM25（30%）+ 向量（70%）融合
- **智能缓存**：重复查询 0ms 响应
- **增量更新**：只重新索引变更文件
- **OpenClaw 集成**：与现有 Mem0 设置协同工作

### 快速开始

```bash
# 搜索
python3 scripts/openclaw-hybrid-memory/scripts/hybrid_search.py "你的查询"

# 查看状态
python3 scripts/openclaw-hybrid-memory/scripts/heartbeat_auto.py --status
```

---

## 📐 Architecture / 架构

![Technical Architecture](https://raw.githubusercontent.com/lamost423/openclaw-hybrid-memory/main/docs/assets/technical-architecture.png)

| Component | Technology | Source |
|-----------|-----------|--------|
| Vector Search | FAISS | Mem0 |
| Graph Memory | Neo4j | Mem0 |
| Keyword Search | BM25 | rank-bm25 |
| Hybrid Fusion | Custom | This Project |
| Caching | In-Memory | This Project |

---

## Documentation / 文档

- [English README](README_EN.md)
- [中文文档](README_CN.md)
- [Architecture Deep Dive](docs/ARCHITECTURE.md)

## License / 许可证

MIT License
