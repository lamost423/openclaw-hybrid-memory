#!/usr/bin/env python3
"""
Heartbeat Automation - 自动化心跳任务执行
定时运行 Compaction Guard 和索引更新
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
VENV_PATH = Path.home() / ".openclaw" / "venv"
STATE_FILE = WORKSPACE / "memory" / "heartbeat-state.json"
LOG_FILE = WORKSPACE / "memory" / "heartbeat-log.json"

def log_event(event_type: str, status: str, details: str = ""):
    """记录心跳日志"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "status": status,
        "details": details
    }
    
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            pass
    
    logs.append(log_entry)
    
    # 只保留最近100条日志
    logs = logs[-100:]
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def run_compaction_guard():
    """运行 Compaction Guard"""
    script = WORKSPACE / "scripts" / "self-memory" / "compaction_guard.py"
    
    if not script.exists():
        log_event("compaction_guard", "error", "Script not found")
        return False
    
    try:
        result = subprocess.run(
            [str(VENV_PATH / "bin" / "python3"), str(script), "--check"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # 解析输出中的备份数量
            output = result.stdout
            if "backed up" in output:
                # 提取备份数量
                import re
                match = re.search(r'(\d+) backed up', output)
                if match:
                    log_event("compaction_guard", "success", f"Backed up {match.group(1)} files")
                else:
                    log_event("compaction_guard", "success", "Check completed")
            else:
                log_event("compaction_guard", "success", "No changes detected")
            return True
        else:
            log_event("compaction_guard", "error", result.stderr[:200])
            return False
    except subprocess.TimeoutExpired:
        log_event("compaction_guard", "error", "Timeout")
        return False
    except Exception as e:
        log_event("compaction_guard", "error", str(e)[:200])
        return False

def run_index_check():
    """检查并更新索引"""
    script = WORKSPACE / "scripts" / "self-memory" / "build_index.py"
    
    if not script.exists():
        log_event("index_check", "error", "Script not found")
        return False
    
    try:
        # 先检查是否需要重建
        result = subprocess.run(
            [str(VENV_PATH / "bin" / "python3"), str(script), "--check"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "needs rebuild: False" in result.stdout:
            log_event("index_check", "success", "Index up to date")
            return True
        
        # 需要重建，执行重建
        result = subprocess.run(
            [str(VENV_PATH / "bin" / "python3"), str(script)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # 提取文档数量
            import re
            match = re.search(r'Documents: (\d+)', result.stdout)
            if match:
                log_event("index_check", "success", f"Rebuilt with {match.group(1)} documents")
            else:
                log_event("index_check", "success", "Index rebuilt")
            return True
        else:
            log_event("index_check", "error", result.stderr[:200])
            return False
            
    except subprocess.TimeoutExpired:
        log_event("index_check", "error", "Timeout")
        return False
    except Exception as e:
        log_event("index_check", "error", str(e)[:200])
        return False

def run_memory_sync():
    """检查 Mem0 状态并记录"""
    try:
        # 简单检查 Neo4j 是否运行
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=neo4j", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "neo4j" in result.stdout:
            log_event("memory_sync", "success", "Neo4j running")
            return True
        else:
            log_event("memory_sync", "warning", "Neo4j not running")
            return False
    except Exception as e:
        log_event("memory_sync", "error", str(e)[:200])
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Heartbeat Automation")
    parser.add_argument("--full", action="store_true", help="Run full check (compaction + index)")
    parser.add_argument("--status", action="store_true", help="Show recent status")
    
    args = parser.parse_args()
    
    if args.status:
        # 显示最近状态
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            print("📊 Recent Heartbeat Activity (last 10):")
            print("-" * 60)
            for log in logs[-10:]:
                time = log['timestamp'][11:19]  # HH:MM:SS
                status_emoji = "✅" if log['status'] == 'success' else "⚠️" if log['status'] == 'warning' else "❌"
                print(f"{time} {status_emoji} {log['type']}: {log['details'][:50]}")
        else:
            print("No heartbeat logs yet")
        return
    
    # 运行完整检查
    print("🔍 Running Heartbeat Automation...")
    print("=" * 60)
    
    results = []
    
    # 1. Compaction Guard
    print("\n1️⃣ Running Compaction Guard...")
    results.append(("Compaction Guard", run_compaction_guard()))
    
    # 2. Index Check
    print("\n2️⃣ Checking Self-Memory Index...")
    results.append(("Index Check", run_index_check()))
    
    # 3. Memory Sync
    print("\n3️⃣ Checking Mem0 Status...")
    results.append(("Mem0 Status", run_memory_sync()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("📋 Summary:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    # 如果全部成功，返回 0，否则返回 1
    if all(r[1] for r in results):
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
