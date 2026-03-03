# HEARTBEAT.md

## 轻量级状态监控

Heartbeat 每 30 分钟检查一次系统状态。
**注意：实际维护任务由 Cron 每小时执行，Heartbeat 只做轻量级状态确认。**

### 检查项

- [ ] 系统整体状态是否正常
- [ ] 是否有紧急事项需要立即汇报

### When To Reach Out
- Reddit cron job failed 2+ times
- Important calendar event < 2h
- New skill deployed and needs testing
- 系统出现紧急异常（如无法连接）

### Default Response
If nothing needs attention → `HEARTBEAT_OK`
