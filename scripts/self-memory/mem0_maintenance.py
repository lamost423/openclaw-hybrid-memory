#!/usr/bin/env python3
"""
Mem0 维护脚本 - 每小时执行
- 导出记忆备份
- 整理今日日志到 Mem0
"""

import os
import sys
import subprocess
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
        result = subprocess.run(
            [
                sys.executable,
                str(WORKSPACE / "scripts" / "mem0_bridge_enhanced.py"),
                "export",
                "--output", str(BACKUP_FILE)
            ],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE),
            env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"}
        )
        
        if result.returncode == 0:
            if BACKUP_FILE.exists():
                size = BACKUP_FILE.stat().st_size
                log(f"✅ Mem0 备份已导出: {BACKUP_FILE} ({size} bytes)")
                return True
            else:
                log("⚠️  备份文件未生成")
                return False
        else:
            log(f"❌ Mem0 备份失败: {result.stderr}")
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
        
        # 提取关键事实（简化版，只取前 1500 字符）
        facts = content[:1500] if len(content) > 1500 else content
        
        # 使用命令行添加记忆
        result = subprocess.run(
            [
                sys.executable,
                str(WORKSPACE / "scripts" / "mem0_bridge_enhanced.py"),
                "add",
                f"{today} 日志摘要: {facts}"
            ],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE),
            env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"}
        )
        
        if result.returncode == 0:
            log(f"✅ 今日日志已同步到 Mem0 ({size} bytes)")
            return True
        else:
            log(f"⚠️  Mem0 同步失败: {result.stderr}")
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
