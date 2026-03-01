# HEARTBEAT.md

## Memory System Maintenance Checklist

Every heartbeat, check if any of these need attention:

### Every Hour (Critical File Protection)
- [ ] Run Heartbeat Automation - 自动化备份、索引更新、Mem0检查
  ```bash
  source ~/.openclaw/venv-py311/bin/activate && python3 scripts/self-memory/heartbeat_auto.py
  ```
  
- [ ] 检查搜索缓存状态
  ```bash
  source ~/.openclaw/venv-py311/bin/activate && python3 scripts/self-memory/search_cache.py --stats
  ```

### Daily (Each Session)
- [ ] Today's log exists: `memory/YYYY-MM-DD.md`
- [ ] Read yesterday's log for context
- [ ] Mem0 同步：将今日新增的重要事实写入 Mem0
  ```bash
  source ~/.openclaw/venv-py311/bin/activate && KMP_DUPLICATE_LIB_OK=TRUE python3 scripts/mem0_bridge_enhanced.py add "事实" --user daniel
  ```

### Every 3 Days
- [ ] Review recent `memory/*.md` files
- [ ] Distill important events to `MEMORY.md`
- [ ] 从 Mem0 导出备份覆盖 MEMORY_BACKUP.md
  ```bash
  source ~/.openclaw/venv-py311/bin/activate && KMP_DUPLICATE_LIB_OK=TRUE python3 scripts/mem0_bridge_enhanced.py export --output MEMORY_BACKUP.md --user daniel
  ```
- [ ] Update `heartbeat-state.json`

### Weekly
- [ ] Archive old daily logs (keep last 30 days)
- [ ] Review and update `SOUL.md` if personality evolved
- [ ] Check `TOOLS.md` for outdated info
- [ ] 检查 Docker 容器健康：`docker ps` 确认 neo4j + xiaohongshu-mcp 在运行

### When To Reach Out
- Reddit cron job failed 2+ times
- Important calendar event < 2h
- New skill deployed and needs testing
- Memory maintenance overdue
- Docker 容器挂了（neo4j / xiaohongshu-mcp）

### Default Response
If nothing needs attention → `HEARTBEAT_OK`
