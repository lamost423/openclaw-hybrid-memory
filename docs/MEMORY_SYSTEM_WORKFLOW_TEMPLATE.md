# Mem0 + Self-Memory 系统自动化工作流程

## 🔄 完整工作流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                        系统工作流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  全天   ┌─────────────┐     ┌─────────────┐                   │
│         │  用户对话    │ ←→  │ SESSION-STATE │ ← HOT层(实时)    │
│         │             │     │   (WAL协议)   │                   │
│         └──────┬──────┘     └─────────────┘                   │
│                │                                                │
│                ▼                                                │
│  每次对话 ┌─────────────┐                                      │
│         │ 提取关键事实  │ → 写入 Mem0 (WARM层)                 │
│         │             │     + 更新文件日志                      │
│         └──────┬──────┘                                      │
│                │                                                │
│                ▼                                                │
│  每30分钟 ┌─────────────┐                                      │
│  (Heartbeat)│ 系统维护   │                                      │
│         │             │                                      │
│         │ ├─ Compaction Guard (备份关键文件)                  │
│         │ ├─ 检查索引更新                                      │
│         │ ├─ 检查Docker容器                                    │
│         │ └─ 其他维护任务                                      │
│         └──────┬──────┘                                      │
│                │                                                │
│                ▼                                                │
│  需要时  ┌─────────────┐                                      │
│         │ 混合搜索     │ ← BM25 + Vector + Cache              │
│         │             │   检索 WARM层 + COLD层                │
│         └──────┬──────┘                                      │
│                │                                                │
│                ▼                                                │
│  每周   ┌─────────────┐                                        │
│         │ 归档旧日志   │ ← 保留最近30天                        │
│         │ 更新 MEMORY  │ ← 提炼长期记忆                        │
│         │ Mem0备份     │ ← 导出备份文件                        │
│         └─────────────┘                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 系统自动运行的部分

### 1. 对话记忆提取
**触发：** 每次用户对话结束  
**执行：**
- 分析对话内容提取关键事实
- 写入 Mem0 (Neo4j + FAISS)
- 更新本地记忆文件

### 2. Heartbeat 维护 (每 30 分钟)
**触发：** OpenClaw Heartbeat  
**执行：**
```bash
# 自动完成：
✓ Compaction Guard (备份关键文件)
✓ 索引状态检查
✓ Mem0 状态检查
✓ Docker 容器健康检查
```

### 3. 搜索优化 (每次查询)
**自动完成：**
```
查询 → 检查缓存 → [命中] → 直接返回 (0ms)
     ↓
   [未命中] → 混合搜索 → 记录历史 → 存入缓存 → 返回结果
```

### 4. 索引维护 (文件变更时)
**触发：** 检测到 memory/ 目录文件变更  
**执行：**
```bash
# 增量更新 (只变更的文件)
python3 scripts/self-memory/incremental_update.py
```

---

## 👤 用户参与的部分

### 日常（每天）
| 任务 | 操作 |
|------|------|
| 与 AI 对话 | 正常聊天、布置任务 |
| 确认重要决策 | 如果有的话 |

### 每周（建议）
| 任务 | 操作 | 命令 |
|------|------|------|
| 查看搜索统计 | 了解查询模式 | `python3 scripts/self-memory/search_cache.py --stats` |
| 清理过期缓存 | 释放空间 | `python3 scripts/self-memory/search_cache.py --clear-expired` |
| 导出 Mem0 备份 | 数据安全 | `python3 scripts/self-memory/mem0_bridge_enhanced.py export` |

---

## 📋 系统状态检查命令

```bash
# 1. 查看系统整体状态
python3 scripts/self-memory/heartbeat_auto.py --status

# 2. 查看缓存统计
python3 scripts/self-memory/search_cache.py --stats

# 3. 查看搜索历史
python3 scripts/self-memory/search_history.py --history

# 4. 查看索引状态
python3 scripts/self-memory/incremental_update.py --status

# 5. 测试搜索功能
python3 scripts/self-memory/mem0_bridge_enhanced.py search "测试查询"
```

---

## ⚠️ 异常情况处理

### 如果搜索变慢了
```bash
# 检查索引状态
python3 scripts/self-memory/incremental_update.py --status

# 如果需要，强制重建索引
python3 scripts/self-memory/build_index.py --force
```

### 如果缓存占用了太多空间
```bash
# 清理过期缓存
python3 scripts/self-memory/search_cache.py --clear-expired

# 或清空所有缓存
python3 scripts/self-memory/search_cache.py --clear
```

### 如果备份文件太多
```bash
# 查看备份目录
ls -la ~/.openclaw/workspace/backups/compaction-guard/

# 手动清理旧备份（保留最近一周的）
```

---

## 🎯 扩展：添加自定义自动化

### 添加定时任务 (Cron)
```bash
# 示例：每天 8:00 执行自定义任务
openclaw cron add \
  --name "daily-custom-task" \
  --cron "0 8 * * *" \
  --session isolated \
  --message "执行你的自定义任务" \
  --announce
```

### 添加个人工作流
在 `HEARTBEAT.md` 中添加自定义检查项：
```markdown
- [ ] 检查邮件
- [ ] 查看日历事件
- [ ] 其他自定义任务
```

---

## 🔧 配置文件说明

### 核心配置文件
| 文件 | 用途 |
|------|------|
| `scripts/mem0_config.py` | Mem0 连接配置（Neo4j、API Key） |
| `HEARTBEAT.md` | 系统维护检查清单 |
| `.gitignore` | Git 排除规则 |

### 数据存储位置
| 目录 | 内容 |
|------|------|
| `memory/` | 每日日志（Git 排除） |
| `config/self-memory/` | 索引和缓存（Git 排除） |
| `backups/` | Compaction Guard 备份（Git 排除） |

---

**现在系统已基本自动化，你的主要工作是：正常对话 + occasional 决策确认。**
