#!/usr/bin/env python3
"""
Build Index Script - 为 Self-Memory 系统创建 BM25 + 向量索引
读取 memory/ 目录所有 .md 文件，生成索引保存到 config/self-memory/index/
"""

import os
import sys
import json
import pickle
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# 添加虚拟环境路径
venv_path = Path.home() / ".openclaw" / "venv"
if venv_path.exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))

from rank_bm25 import BM25Okapi


class IndexBuilder:
    """索引构建器 - 支持 BM25 和向量索引"""
    
    def __init__(self):
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.memory_dir = self.workspace / "memory"
        self.index_dir = self.workspace / "config" / "self-memory" / "index"
        self.ollama_url = "http://localhost:11434/api/embeddings"
        
        # 确保索引目录存在
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 文档存储
        self.documents = []
        self.tokenized_corpus = []
        self.embeddings = []
        
    def tokenize(self, text: str) -> List[str]:
        """中文分词（字符级 + 英文单词提取）"""
        import re
        # 提取中文字符、英文单词和数字
        tokens = re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+|\d+', text.lower())
        return tokens
    
    def get_embedding(self, text: str) -> List[float]:
        """使用 Ollama 获取文本的 embedding"""
        import requests
        try:
            # 限制文本长度避免过长
            text = text[:2000]
            response = requests.post(
                self.ollama_url,
                json={"model": "mxbai-embed-large", "prompt": text},
                timeout=60
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"  ⚠️  Embedding error: {e}")
            return []
    
    def load_documents(self) -> List[Dict]:
        """从 memory 目录加载所有 .md 文件"""
        documents = []
        
        if not self.memory_dir.exists():
            print(f"⚠️  Memory directory not found: {self.memory_dir}")
            return documents
        
        for md_file in sorted(self.memory_dir.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                stat = md_file.stat()
                
                documents.append({
                    "id": md_file.stem,
                    "filename": md_file.name,
                    "content": content,
                    "path": str(md_file.relative_to(self.workspace)),
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "word_count": len(content.split())
                })
            except Exception as e:
                print(f"  ⚠️  Error reading {md_file}: {e}")
        
        return documents
    
    def build_bm25_index(self) -> BM25Okapi:
        """构建 BM25 索引"""
        print("🔨 Building BM25 index...")
        
        self.tokenized_corpus = []
        for doc in self.documents:
            # 分词标题和内容
            text = f"{doc['filename']} {doc['content']}"
            tokens = self.tokenize(text)
            self.tokenized_corpus.append(tokens)
        
        bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"  ✓ Indexed {len(self.documents)} documents for BM25")
        return bm25
    
    def build_vector_index(self) -> np.ndarray:
        """构建向量索引（使用 Ollama）"""
        print("🧠 Building vector index with Ollama...")
        
        embeddings = []
        for i, doc in enumerate(self.documents):
            print(f"  Processing {i+1}/{len(self.documents)}: {doc['filename']}", end="\r")
            
            # 提取文档前1000字符作为 embedding 输入
            text = f"{doc['filename']}: {doc['content'][:800]}"
            embedding = self.get_embedding(text)
            
            if embedding:
                embeddings.append(embedding)
            else:
                # 如果失败，使用零向量占位
                print(f"\n  ⚠️  Failed to get embedding for {doc['filename']}")
                embeddings.append([0.0] * 1024)  # mxbai-embed-large 是 1024 维
        
        print(f"\n  ✓ Generated {len(embeddings)} embeddings")
        return np.array(embeddings, dtype=np.float32)
    
    def save_index(self, bm25: BM25Okapi, embeddings: np.ndarray):
        """保存索引到文件"""
        print("💾 Saving index files...")
        
        # 保存 BM25 索引
        bm25_path = self.index_dir / "bm25_index.pkl"
        with open(bm25_path, "wb") as f:
            pickle.dump({
                "bm25": bm25,
                "tokenized_corpus": self.tokenized_corpus
            }, f)
        print(f"  ✓ BM25 index saved: {bm25_path}")
        
        # 保存向量索引
        vector_path = self.index_dir / "vector_index.npy"
        np.save(vector_path, embeddings)
        print(f"  ✓ Vector index saved: {vector_path}")
        
        # 保存文档元数据（不包含完整内容，避免重复）
        metadata = []
        for doc in self.documents:
            metadata.append({
                "id": doc["id"],
                "filename": doc["filename"],
                "path": doc["path"],
                "size": doc["size"],
                "mtime": doc["mtime"],
                "word_count": doc["word_count"]
            })
        
        meta_path = self.index_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "document_count": len(self.documents),
                "embedding_dim": embeddings.shape[1] if len(embeddings) > 0 else 0,
                "documents": metadata
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Metadata saved: {meta_path}")
        
        # 保存完整文档内容（供搜索使用）
        docs_path = self.index_dir / "documents.json"
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False)
        print(f"  ✓ Documents saved: {docs_path}")
        
        # 计算并保存索引哈希（用于增量更新检测）
        index_hash = self.compute_index_hash()
        hash_path = self.index_dir / "index.hash"
        hash_path.write_text(index_hash)
        print(f"  ✓ Index hash saved: {hash_path}")
    
    def compute_index_hash(self) -> str:
        """计算索引内容的哈希值"""
        hasher = hashlib.sha256()
        for doc in sorted(self.documents, key=lambda x: x["id"]):
            hasher.update(f"{doc['id']}:{doc['mtime']}".encode())
        return hasher.hexdigest()[:16]
    
    def check_needs_rebuild(self) -> bool:
        """检查是否需要重建索引"""
        hash_path = self.index_dir / "index.hash"
        
        if not hash_path.exists():
            return True
        
        current_hash = self.compute_index_hash()
        stored_hash = hash_path.read_text().strip()
        
        return current_hash != stored_hash
    
    def build(self, force: bool = False) -> Dict:
        """执行完整的索引构建流程"""
        print("=" * 60)
        print("Self-Memory Index Builder")
        print("=" * 60)
        
        # 加载文档
        print(f"\n📁 Loading documents from {self.memory_dir}...")
        self.documents = self.load_documents()
        
        if not self.documents:
            print("⚠️  No documents found!")
            return {"success": False, "error": "No documents"}
        
        print(f"  ✓ Loaded {len(self.documents)} documents")
        
        # 检查是否需要重建
        if not force:
            needs_rebuild = self.check_needs_rebuild()
            if not needs_rebuild:
                print("\n✅ Index is up to date. Use --force to rebuild.")
                return {"success": True, "rebuilt": False}
        
        # 构建索引
        print(f"\n🔨 Building indexes...")
        bm25 = self.build_bm25_index()
        embeddings = self.build_vector_index()
        
        # 保存索引
        self.save_index(bm25, embeddings)
        
        print(f"\n✅ Index build complete!")
        print(f"   Documents: {len(self.documents)}")
        print(f"   Embedding dim: {embeddings.shape[1]}")
        print(f"   Index location: {self.index_dir}")
        
        return {
            "success": True,
            "rebuilt": True,
            "document_count": len(self.documents),
            "embedding_dim": embeddings.shape[1]
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Self-Memory Index")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if up to date")
    parser.add_argument("--check", action="store_true", help="Check if rebuild is needed")
    
    args = parser.parse_args()
    
    builder = IndexBuilder()
    
    if args.check:
        needs_rebuild = builder.check_needs_rebuild()
        print(f"Index needs rebuild: {needs_rebuild}")
        sys.exit(0 if not needs_rebuild else 1)
    
    result = builder.build(force=args.force)
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
