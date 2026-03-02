# OpenClaw Cron vs Heartbeat 机制详解

## 核心区别

| 特性 | Cron | Heartbeat |
|------|------|-----------|
| **触发机制** | 精确时间调度 | 定期唤醒检查 |
| **执行环境** | Isolated session（独立） | Main session（有对话上下文） |
| **用途** | 定时任务、自动化操作 | 状态监控、轻量级检查 |
| **执行逻辑** | 执行预定义脚本/命令 | Agent 根据 prompt 自主决策 |
| **日志记录** | 详细执行日志 | 仅 Gateway 层面日志，无执行细节 |
| **最佳实践** | 重任务、需精确时间 | 轻检查、上下文感知决策 |

---

## Cron 机制

### 工作原理
```
Gateway 调度器 → 到达时间点 → 创建 Isolated Session → 执行 payload → 记录结果 → 可选发送通知
```

### 配置示例
```json
{
  "name": "self-memory-maintenance",
  "schedule": {
    "kind": "cron",
    "expr": "0 * * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行维护任务...",
    "model": "kimi-coding/k2p5"
  },
  "delivery": {
    "mode": "announce",
    "channel": "telegram",
    "to": "5491188388"
  }
}
```

### 适用场景
- ✅ 定时数据备份
- ✅ 定期系统维护
- ✅ 定时简报生成
- ✅ 需要精确时间的任务

### 关键配置
| 配置项 | 说明 |
|--------|------|
| `sessionTarget: isolated` | 在独立 session 执行，不影响主对话 |
| `delivery.mode: announce` | 执行结果发送到指定频道 |
| `delivery.mode: none` | 静默执行，不发送通知 |

---

## Heartbeat 机制

### 工作原理
```
Gateway 定时器 → 发送 prompt 到 Main Session → Agent 读取 HEARTBEAT.md → 自主检查 → 回复 HEARTBEAT_OK 或汇报
```

### 配置位置
`~/.openclaw/workspace/HEARTBEAT.md`

### 配置示例
```markdown
## 轻量级状态监控

- [ ] 系统整体状态是否正常
- [ ] 是否有紧急事项需要立即汇报

### When To Reach Out
- Important calendar event < 2h
- 系统出现紧急异常

### Default Response
If nothing needs attention → `HEARTBEAT_OK`
```

### 适用场景
- ✅ 轻量级状态检查
- ✅ 需要对话上下文的决策
- ✅ 智能判断是否打扰用户
- ✅ 监控类任务（非执行类）

### 关键特性
| 特性 | 说明 |
|------|------|
| Context-aware | 能参考对话历史做决策 |
| Smart suppression | 无异常时静默（HEARTBEAT_OK） |
| Natural timing | 时间可轻微漂移，非精确 |

---

## 常见误区

### ❌ 误区 1：Heartbeat 会执行 HEARTBEAT.md 中的命令
**事实：** Heartbeat 发送 prompt 让 agent 读取 HEARTBEAT.md，agent **自主决定**是否执行，不是自动执行。

### ❌ 误区 2：Heartbeat 和 Cron 可以做同样的事
**事实：**
- Cron 执行**具体任务**（有明确执行逻辑）
- Heartbeat 做**状态检查**（agent 自主决策）

### ❌ 误区 3：Heartbeat 有详细执行日志
**事实：** Heartbeat 只有 Gateway 层面的启动日志，**没有** agent 执行检查内容的详细记录。

---

## 最佳实践

### 选择 Cron 当：
- 需要精确时间执行
- 任务较重，需要隔离执行
- 需要确保任务被执行（非 agent 自主决策）
- 需要详细执行日志

### 选择 Heartbeat 当：
- 轻量级状态检查
- 需要根据对话上下文做决策
- 智能判断是否打扰用户
- 监控类任务（检查而非执行）

### 组合使用
```
Cron:    每小时执行实际维护任务（备份、索引更新）
         ↓
Heartbeat: 每 30 分钟检查是否有紧急事项需要汇报
```

**不要重复：** 避免在 Heartbeat 和 Cron 中配置相同的检查项。

---

## 实际配置参考

### 当前配置

| 任务 | 机制 | 频率 | 用途 |
|------|------|------|------|
| Self-Memory 维护 | Cron | 每小时 | 执行备份、索引更新、Mem0检查 |
| 早安简报 | Cron | 每天 07:00 | 生成并发送简报 |
| 轻量级监控 | Heartbeat | 每 30 分钟 | 检查紧急事项 |

### 经验教训
1. Cron 负责**执行**，Heartbeat 负责**监控**
2. Cron 必须有 `delivery: announce` 才能收到通知
3. Heartbeat 不要配置具体执行命令（agent 可能不执行）
4. 重任务放 Cron，轻检查放 Heartbeat

---

## 推荐配置方案

### 生产环境推荐配置

#### 1. Cron 任务配置（执行类）

**记忆系统维护（每小时）**
```bash
openclaw cron add \
  --name "memory-maintenance" \
  --cron "0 * * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "执行记忆系统维护：\n\nsource ~/.openclaw/venv-py311/bin/activate && cd ~/.openclaw/workspace\n\n# 1. Self-Memory 维护\nKMP_DUPLICATE_LIB_OK=TRUE python3 scripts/self-memory/heartbeat_auto.py --full\n\n# 2. Mem0 维护\nKMP_DUPLICATE_LIB_OK=TRUE python3 scripts/self-memory/mem0_maintenance.py" \
  --announce \
  --channel telegram \
  --to "YOUR_TELEGRAM_ID"
```

**关键要点：**
- `--session isolated`：隔离执行，不影响主会话
- `--announce`：执行结果发送到 Telegram
- 同时维护 Self-Memory（FAISS+BM25）和 Mem0（Neo4j）

#### 2. Heartbeat 配置（监控类）

**HEARTBEAT.md 推荐内容：**
```markdown
## 轻量级状态监控

Every heartbeat, check if any of these need attention:

### 紧急事项检查
- [ ] 系统整体状态是否正常
- [ ] Docker 容器是否运行（neo4j / xiaohongshu-mcp）
- [ ] Cron 任务是否连续失败 2+ 次

### When To Reach Out
- Docker 容器挂了且自动重启失败
- 搜索缓存命中率 < 50%
- 平均搜索响应时间 > 1s
- 重要日历事件 < 2h

### Default Response
If nothing needs attention → `HEARTBEAT_OK`
```

**关键要点：**
- 只做**检查**，不做**执行**
- 发现问题才汇报，无异常静默

#### 3. 分层维护策略

| 层级 | 组件 | 维护方式 | 频率 |
|------|------|----------|------|
| **HOT** | SESSION-STATE.md | Compaction Guard 备份 | Cron 每小时 |
| **WARM** | Mem0 (Neo4j) | 导出备份 + 日志同步 | Cron 每小时 |
| **COLD** | Self-Memory (FAISS) | 索引重建 + 检查 | Cron 每小时 |
| **ARCHIVE** | MEMORY_BACKUP.md | 自动导出 | Cron 每小时 |
| **监控** | 系统状态 | Heartbeat 检查 | 每 30 分钟 |

#### 4. 避免重复

**❌ 错误做法：**
- Heartbeat 中写具体执行命令（agent 可能不执行）
- Cron 和 Heartbeat 做同样的检查

**✅ 正确做法：**
- Cron：执行具体维护脚本
- Heartbeat：轻量级状态检查

### 部署步骤

1. **复制代码到 workspace**
   ```bash
   git clone https://github.com/lamost423/openclaw-hybrid-memory.git ~/.openclaw/workspace
   ```

2. **配置 Python 环境**
   ```bash
   python3.11 -m venv ~/.openclaw/venv-py311
   source ~/.openclaw/venv-py311/bin/activate
   pip install -r requirements.txt
   ```

3. **启动依赖服务**
   ```bash
   docker start neo4j
   docker start xiaohongshu-mcp  # 可选
   ollama serve  # 本地 embedding 服务
   ```

4. **配置 Mem0**
   编辑 `scripts/mem0_config.py`，设置 API key

5. **创建 Cron 任务**（按上述推荐配置）

6. **配置 Heartbeat**
   创建 `HEARTBEAT.md`（按上述推荐内容）

7. **测试**
   ```bash
   openclaw cron run memory-maintenance
   ```
