# Reddit 自动化方案 V2.0 - PRAW 专业版

## 技术栈升级

### 旧方案 (失败)
AppleScript → Chrome → JavaScript → Reddit
❌ GUI 依赖 ❌ 时序问题 ❌ 权限问题

### 新方案 (推荐)
Python + PRAW → Reddit API
✅ 纯代码 ✅ 无浏览器 ✅ Cron 完美支持

## 核心组件

### 1. PRAW (Python Reddit API Wrapper)
```bash
pip install praw
```

### 2. 配置文件 praw.ini
```ini
[DEFAULT]
client_id=YOUR_CLIENT_ID
client_secret=YOUR_SECRET
username=Few_Finish_2500
password=YOUR_PASSWORD
user_agent=script:reddit_cultivate:v1.0 (by u/Few_Finish_2500)
```

### 3. 主脚本 reddit_bot.py
- 自动 rate limit 控制
- 数据库去重
- 智能评论生成
- 完整日志记录

## 执行计划

| 时间 | 操作 |
|------|------|
| 01:00 | 启动脚本，检查9个 subreddit |
| 01:00-01:30 | 发3条评论（自动间隔2分钟）|
| 03:00 | 第2轮执行 |
| 05:00 | 第3轮执行 |
| 06:30 | 生成日报 |

## 优势

1. **稳定性** - PRAW 自动处理 rate limit，不会被封
2. **去重** - SQLite 数据库存储已发帖记录
3. **智能评论** - 根据帖子内容调用 LLM 生成
4. **无人值守** - Cron 直接运行 Python 脚本
5. **可监控** - 详细日志，出错自动通知

## 下一步

1. 申请 Reddit API 凭证
2. 安装 PRAW
3. 部署脚本
4. 设置 Cron
