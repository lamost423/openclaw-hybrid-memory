# 长任务后台化执行规范

## 原则

**任何预计执行时间超过 5 秒的任务，必须使用 `background: true`**

## 触发条件

| 场景 | 示例 | 处理方式 |
|------|------|----------|
| 文件操作 | 大批量文件读写、压缩解压 | `background: true` |
| 网络请求 | API 调用、下载、上传 | `background: true` |
| 代码执行 | Python 脚本、构建、测试 | `background: true` |
| 复杂搜索 | 大规模向量检索、全网爬虫 | `background: true` |
| 外部工具 | ffmpeg、数据处理工具 | `background: true` |

## 执行流程

```
1. 预估任务时间
   ↓
2. >5s ? 使用 background: true
   ↓
3. 记录 sessionId
   ↓
4. 轮询 process(action=poll) 获取结果
   ↓
5. 完成后汇报结果
```

## 代码模板

```javascript
// 启动后台任务
const { sessionId } = await exec({
  command: "long-running-command",
  background: true,
  yieldMs: 5000  // 5秒后自动后台化（已配置）
});

// 轮询获取结果
const result = await process({
  action: "poll",
  sessionId: sessionId,
  timeout: 60000  // 最多等60秒
});
```

## 用户沟通

启动后台任务时，告知用户：
- "任务已转后台执行，预计需要 X 秒"
- "完成后我会主动汇报结果"

## 例外情况

以下情况可以 inline 执行：
- 简单的文件读取（<5秒）
- 快速的内存查询
- 用户明确要求实时反馈的简单操作

---
_创建时间: 2026-03-02_
