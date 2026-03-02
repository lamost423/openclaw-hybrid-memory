#!/usr/bin/env python3
"""
Incremental Index Update - 增量索引更新
只更新变更的文件，不重建全量索引
"""

import os
import sys
import json
import pickle
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Set, Tuple
from datetime import datetime

# 添加虚拟环境路径
venv_path = Path.home() / ".openclaw" / "venv"
if venv_path.exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))

from rank_bm25 import BM25Okapi

class IncrementalIndexManager:
    """增量索引管理器"""
    
    def __init__(self):
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.memory_dir = self.workspace / "memory"
        self.index_dir = self.workspace / "config" / "self-memory" / "index"
        
        # 索引文件路径
        self.bm25_file = self.index_dir / "bm25_index.pkl"
        self.vector_file = self.index_dir / "vector_index.npy"
        self.docs_file = self.index_dir / "documents.json"
        self.meta_file = self.index_dir / "metadata.json"
        self.hash_file = self.index_dir / "index.hash"
        self.state_file = self.index_dir / "incremental_state.json"
        
        self.ollama_url = "http://localhost:11434/api/embeddings"
    
    def _load_state(self) -> Dict:
        """加载增量更新状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_full_build": None,
            "file_hashes": {},
            "total_updates": 0
        }
    
    def _save_state(self, state: Dict):
        """保存增量更新状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    def _compute_file_hash(self, filepath: Path) -> str:
        """计算文件哈希"""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()[:16]
        except:
            return ""
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本向量"""
        import requests
        try:
            response = requests.post(
                self.ollama_url,
                json={"model": "mxbai-embed-large", "prompt": text[:2000]},
                timeout=30
            )
            response.raise_for_status()
            return np.array(response.json()["embedding"])
        except Exception as e:
            print(f"  ⚠️  Embedding error: {e}")
            return np.zeros(1024)
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        import re
        return re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+|\d+', text.lower())
    
    def scan_changes(self) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        扫描文件变更
        返回: (新增文件, 修改文件, 删除文件)
        """
        state = self._load_state()
        
        # 获取当前所有 .md 文件
        current_files = set(self.memory_dir.glob("*.md"))
        current_paths = {str(f.relative_to(self.workspace)): f for f in current_files}
        
        # 获取之前记录的文件
        previous_files = set(state["file_hashes"].keys())
        
        # 检测新增、修改、删除
        added = []
        modified = []
        deleted = []
        
        for path, filepath in current_paths.items():
            if path not in previous_files:
                added.append(filepath)
            else:
                current_hash = self._compute_file_hash(filepath)
                if current_hash != state["file_hashes"][path]:
                    modified.append(filepath)
        
        for path in previous_files:
            if path not in current_paths:
                deleted.append(Path(self.workspace) / path)
        
        return added, modified, deleted
    
    def incremental_update(self) -> bool:
        """执行增量更新"""
        print("🔍 Scanning for changes...")
        added, modified, deleted = self.scan_changes()
        
        if not added and not modified and not deleted:
            print("✅ No changes detected, index up to date")
            return True
        
        print(f"📊 Changes detected:")
        print(f"   + Added: {len(added)}")
        print(f"   ~ Modified: {len(modified)}")
        print(f"   - Deleted: {len(deleted)}")
        
        # 如果没有现有索引，执行全量重建
        if not self.bm25_file.exists():
            print("\n🔄 No existing index, performing full rebuild...")
            return self.full_rebuild()
        
        # 加载现有索引
        try:
            with open(self.docs_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            with open(self.bm25_file, 'rb') as f:
                bm25_data = pickle.load(f)
            
            embeddings = np.load(self.vector_file)
            
            state = self._load_state()
        except Exception as e:
            print(f"⚠️  Failed to load existing index: {e}")
            print("🔄 Performing full rebuild...")
            return self.full_rebuild()
        
        # 处理删除
        for filepath in deleted:
            path_str = str(filepath.relative_to(self.workspace))
            documents = [d for d in documents if d.get("path") != path_str]
            if path_str in state["file_hashes"]:
                del state["file_hashes"][path_str]
        
        # 处理修改（删除旧的，稍后添加新的）
        for filepath in modified:
            path_str = str(filepath.relative_to(self.workspace))
            documents = [d for d in documents if d.get("path") != path_str]
        
        # 处理新增和修改（都视为新文档）
        new_files = added + modified
        
        if new_files:
            print(f"\n🔄 Processing {len(new_files)} files...")
            
            new_documents = []
            new_embeddings = []
            
            for i, filepath in enumerate(new_files):
                print(f"  {i+1}/{len(new_files)}: {filepath.name}")
                
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                path_str = str(filepath.relative_to(self.workspace))
                
                doc = {
                    "id": filepath.stem,
                    "content": content,
                    "path": path_str,
                    "title": filepath.name,
                    "updated": datetime.now().isoformat()
                }
                
                new_documents.append(doc)
                
                # 生成向量
                embedding = self._get_embedding(content[:1500])
                new_embeddings.append(embedding)
                
                # 更新状态
                state["file_hashes"][path_str] = self._compute_file_hash(filepath)
            
            # 合并文档和向量
            documents.extend(new_documents)
            if new_embeddings:
                embeddings = np.vstack([embeddings, np.array(new_embeddings)])
        
        # 重建 BM25 索引（必须全量重建）
        print("\n🔨 Rebuilding BM25 index...")
        tokenized = [self._tokenize(d["content"]) for d in documents]
        bm25 = BM25Okapi(tokenized)
        
        # 保存索引
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.docs_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        with open(self.bm25_file, 'wb') as f:
            pickle.dump(bm25, f)
        
        np.save(self.vector_file, embeddings)
        
        # 更新状态
        state["last_full_build"] = datetime.now().isoformat()
        state["total_updates"] = state.get("total_updates", 0) + 1
        self._save_state(state)
        
        print(f"\n✅ Incremental update complete!")
        print(f"   Total documents: {len(documents)}")
        print(f"   Embedding dim: {embeddings.shape[1]}")
        print(f"   Total updates: {state['total_updates']}")
        
        return True
    
    def full_rebuild(self) -> bool:
        """执行全量重建"""
        # 调用 build_index.py
        import subprocess
        result = subprocess.run(
            [sys.executable, str(self.workspace / "scripts" / "self-memory" / "build_index.py")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # 重置状态
            state = {
                "last_full_build": datetime.now().isoformat(),
                "file_hashes": {},
                "total_updates": 1
            }
            
            # 记录所有文件哈希
            for f in self.memory_dir.glob("*.md"):
                path_str = str(f.relative_to(self.workspace))
                state["file_hashes"][path_str] = self._compute_file_hash(f)
            
            self._save_state(state)
            return True
        else:
            print(f"❌ Full rebuild failed: {result.stderr}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental Index Update")
    parser.add_argument("--full", action="store_true", help="Force full rebuild")
    parser.add_argument("--status", action="store_true", help="Show incremental status")
    
    args = parser.parse_args()
    
    manager = IncrementalIndexManager()
    
    if args.status:
        state = manager._load_state()
        added, modified, deleted = manager.scan_changes()
        
        print("📊 Incremental Index Status:")
        print("-" * 60)
        print(f"Last full build: {state.get('last_full_build', 'Never')}")
        print(f"Total updates: {state.get('total_updates', 0)}")
        print(f"Tracked files: {len(state.get('file_hashes', {}))}")
        print(f"\nPending changes:")
        print(f"  + Added: {len(added)}")
        print(f"  ~ Modified: {len(modified)}")
        print(f"  - Deleted: {len(deleted)}")
    
    elif args.full:
        success = manager.full_rebuild()
        sys.exit(0 if success else 1)
    
    else:
        success = manager.incremental_update()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
