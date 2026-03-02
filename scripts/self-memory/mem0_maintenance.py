#!/usr/bin/env python3
"""
Mem0 维护脚本 - 每小时执行
- 导出记忆备份
- 整理今日日志到 Mem0
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
BACKUP_FILE = WORKSPACE / "MEMORY_BACKUP.md"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def export_mem0_backup():
    """导出 Mem0 备份"""
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from mem0_bridge_enhanced import MemoryEngine
        
        engine = MemoryEngine()
        if not engine.available:
            log("⚠️  Mem0 不可用，跳过备份")
            return False
        
        # 执行导出
        result = engine.export_all()
        if result:
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                f.write(result)
            log(f"✅ Mem0 备份已导出: {BACKUP_FILE}")
            return True
        else:
            log("⚠️  Mem0 导出为空")
            return False
            
    except Exception as e:
        log(f"❌ Mem0 备份失败: {e}")
        return False

def sync_daily_log_to_mem0():
    """将今日日志同步到 Mem0"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = MEMORY_DIR / f"{today}.md"
    
    if not log_file.exists():
        log(f"📭 今日日志不存在: {log_file}")
        return False
    
    # 检查文件大小（小于 500 字节认为内容太少）
    size = log_file.stat().st_size
    if size < 500:
        log(f"📭 今日日志内容太少 ({size} bytes)，跳过同步")
        return False
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取关键事实（简化版，只取前 2000 字符）
        facts = content[:2000] if len(content) > 2000 else content
        
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from mem0_bridge_enhanced import MemoryEngine
        
        engine = MemoryEngine()
        if not engine.available:
            log("⚠️  Mem0 不可用，跳过同步")
            return False
        
        # 写入 Mem0
        success = engine.add(f"2026-03-02 日志摘要: {facts[:500]}...", user_id="daniel")
        if success:
            log(f"✅ 今日日志已同步到 Mem0 ({size} bytes)")
            return True
        else:
            log("⚠️  Mem0 同步失败")
            return False
            
    except Exception as e:
        log(f"❌ 日志同步失败: {e}")
        return False

def main():
    log("=" * 50)
    log("Mem0 维护任务开始")
    log("=" * 50)
    
    # 1. 导出备份
    backup_ok = export_mem0_backup()
    
    # 2. 同步今日日志
    sync_ok = sync_daily_log_to_mem0()
    
    log("=" * 50)
    log(f"维护完成: 备份={'✅' if backup_ok else '❌'}, 同步={'✅' if sync_ok else '❌'}")
    log("=" * 50)

if __name__ == "__main__":
    main()
