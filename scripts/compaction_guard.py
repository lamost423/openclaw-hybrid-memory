#!/usr/bin/env python3
"""
Compaction Guard - 防止上下文压缩丢失关键记忆
监控关键文件变更并自动备份
"""

import os
import sys
import json
import hashlib
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class CompactionGuard:
    """Compaction Guard - 关键文件备份系统"""
    
    def __init__(self, config_path: str = None):
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.backup_dir = self.workspace / "backups" / "compaction-guard"
        self.state_file = self.workspace / "config" / "self-memory" / "guard-state.json"
        
        # 关键文件列表
        self.critical_files = [
            "SESSION-STATE.md",
            "MEMORY.md",
            "SOUL.md",
            "USER.md",
            "knowledge/README.md",
            "knowledge/INDEX.md"
        ]
        
        # 冷却期（秒）
        self.cooldown = 900  # 15分钟
        
        # 加载状态
        self.state = self.load_state()
    
    def load_state(self) -> Dict:
        """加载备份状态"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {"last_backup": {}, "file_hashes": {}}
    
    def save_state(self):
        """保存备份状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))
    
    def compute_hash(self, filepath: Path) -> str:
        """计算文件 SHA256 哈希"""
        if not filepath.exists():
            return ""
        
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""
    
    def should_backup(self, relative_path: str) -> bool:
        """检查是否需要备份"""
        filepath = self.workspace / relative_path
        
        if not filepath.exists():
            return False
        
        current_hash = self.compute_hash(filepath)
        stored_hash = self.state.get("file_hashes", {}).get(relative_path)
        last_backup_time = self.state.get("last_backup", {}).get(relative_path, 0)
        
        # 文件未变更
        if current_hash == stored_hash:
            return False
        
        # 检查冷却期
        current_time = time.time()
        if current_time - last_backup_time < self.cooldown:
            return False
        
        return True
    
    def backup_file(self, relative_path: str) -> bool:
        """备份单个文件"""
        rel_path = Path(relative_path)
        source = self.workspace / relative_path
        
        if not source.exists():
            print(f"  ⚠️  Source not found: {relative_path}")
            return False
        
        # 创建备份路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"
        backup_path = self.backup_dir / rel_path.parent / backup_name
        
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup_path)
            
            # 更新状态
            self.state["file_hashes"][relative_path] = self.compute_hash(source)
            self.state["last_backup"][relative_path] = time.time()
            
            print(f"  ✅ Backed up: {relative_path} -> {backup_path.relative_to(self.backup_dir)}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to backup {relative_path}: {e}")
            return False
    
    def check_and_backup(self, force: bool = False) -> Dict:
        """检查并备份变更文件"""
        results = {"backed_up": [], "skipped": [], "errors": []}
        
        print(f"Compaction Guard Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        
        for relative_path in self.critical_files:
            rel_path = Path(relative_path)
            
            if force or self.should_backup(relative_path):
                if self.backup_file(relative_path):
                    results["backed_up"].append(relative_path)
                else:
                    results["errors"].append(relative_path)
            else:
                results["skipped"].append(relative_path)
                print(f"  ⏭️  Skipped: {relative_path}")
        
        # 保存状态
        self.save_state()
        
        print("-" * 50)
        print(f"Summary: {len(results['backed_up'])} backed up, "
              f"{len(results['skipped'])} skipped, "
              f"{len(results['errors'])} errors")
        
        return results
    
    def list_backups(self, relative_path: str = None):
        """列出备份文件"""
        if relative_path:
            backup_subdir = self.backup_dir / Path(relative_path).parent
            pattern = f"{Path(relative_path).stem}_*"
            backups = list(backup_subdir.glob(pattern))
        else:
            backups = list(self.backup_dir.rglob("*_*.md"))
        
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        print(f"\nBackup Files ({len(backups)} total):")
        print("-" * 50)
        
        for backup in backups[:20]:  # 只显示最近20个
            rel_path = backup.relative_to(self.backup_dir)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            size = backup.stat().st_size
            print(f"  {rel_path}")
            print(f"    Size: {size} bytes | Time: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if len(backups) > 20:
            print(f"  ... and {len(backups) - 20} more")
    
    def restore_backup(self, relative_path: str, timestamp: str = None):
        """恢复备份"""
        if timestamp:
            # 恢复特定时间戳的备份
            backup_name = f"{Path(relative_path).stem}_{timestamp}{Path(relative_path).suffix}"
            backup_path = self.backup_dir / relative_path.parent / backup_name
        else:
            # 恢复最新的备份
            backup_subdir = self.backup_dir / Path(relative_path).parent
            pattern = f"{Path(relative_path).stem}_*"
            backups = list(backup_subdir.glob(pattern))
            
            if not backups:
                print(f"No backups found for {relative_path}")
                return False
            
            backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            backup_path = backups[0]
        
        if not backup_path.exists():
            print(f"Backup not found: {backup_path}")
            return False
        
        # 恢复
        target = self.workspace / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # 先备份当前版本
        current_backup = target.parent / f"{target.stem}_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{target.suffix}"
        if target.exists():
            shutil.copy2(target, current_backup)
        
        shutil.copy2(backup_path, target)
        print(f"✅ Restored: {backup_path.name} -> {target}")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compaction Guard - Protect critical memory files")
    parser.add_argument("--check", action="store_true", help="Check and backup changed files")
    parser.add_argument("--force", action="store_true", help="Force backup (ignore cooldown)")
    parser.add_argument("--list", metavar="PATH", nargs="?", const="", 
                        help="List backups (optionally for specific path)")
    parser.add_argument("--restore", metavar="PATH", help="Restore backup for path")
    parser.add_argument("--timestamp", help="Specific timestamp to restore")
    
    args = parser.parse_args()
    
    guard = CompactionGuard()
    
    if args.check or args.force:
        guard.check_and_backup(force=args.force)
    elif args.list is not None:
        guard.list_backups(args.list if args.list else None)
    elif args.restore:
        guard.restore_backup(args.restore, args.timestamp)
    else:
        # 默认执行检查
        guard.check_and_backup()

if __name__ == "__main__":
    main()
