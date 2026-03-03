# Hybrid Memory Automation

## WARM Layer - Hook Implementation

### 方案：Prompt 标记触发

**机制**：
- 我在回复重要信息时自动添加 `#save` 标记
- 标记触发 `m.add()` 自动执行

**实现**：
```python
# 在我的回复生成后检测
def post_response_hook(response):
    if "#save" in response or is_important_fact(response):
        facts = extract_facts(response)
        for fact in facts:
            m.add(fact, user_id="daniel")
```

**优点**：
- 无需修改 OpenClaw Gateway
- 精确控制哪些内容存入记忆
- 符合现有工具调用模式

---

## COLD Layer - Cron Implementation

### 定时任务：每日 23:00

**任务**：`daily-cold-sync`

**流程**：
1. 读取当日 WARM 新增记忆
2. 整理到 `memory/YYYY-MM-DD.md`
3. 提取重要决策 → 更新 `MEMORY.md`
4. 发送日报到 Telegram

**命令**：
```bash
openclaw cron add \
  --name "daily-cold-sync" \
  --cron "0 23 * * *" \
  --message "Sync WARM to COLD layer" \
  --session isolated \
  --announce
```

---

## 状态

- [ ] WARM Hook - 待实施
- [ ] COLD Cron - 待实施
