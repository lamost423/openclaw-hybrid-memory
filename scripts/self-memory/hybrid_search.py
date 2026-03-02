#!/usr/bin/env python3
"""
混合搜索脚本 - BM25 + FAISS 向量搜索融合
用于增强 Mem0 的搜索能力
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from rank_bm25 import BM25Okapi

# 添加虚拟环境路径
venv_path = Path.home() / ".openclaw" / "venv"
if venv_path.exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))

class HybridSearch:
    """混合搜索：BM25关键词 + 向量语义搜索"""
    
    def __init__(self, vector_weight: float = 0.7, bm25_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.bm25 = None
        self.corpus = []
        self.tokenized_corpus = []
        self.ollama_url = "http://localhost:11434/api/embeddings"
        
    def tokenize(self, text: str) -> List[str]:
        """简单的中文分词（基于字符）"""
        # 对于中文，我们使用字符级分词 + 简单的词语提取
        import re
        # 提取中文字符和英文单词
        tokens = re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+|\d+', text.lower())
        return tokens
    
    def get_embedding(self, text: str) -> List[float]:
        """使用 Ollama 获取文本的 embedding"""
        import requests
        try:
            response = requests.post(
                self.ollama_url,
                json={"model": "mxbai-embed-large", "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []
    
    def index_documents(self, documents: List[Dict]):
        """索引文档集合"""
        self.corpus = documents
        self.tokenized_corpus = []
        
        for doc in documents:
            text = doc.get("content", "")
            tokens = self.tokenize(text)
            self.tokenized_corpus.append(tokens)
        
        # 初始化 BM25
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"Indexed {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """执行混合搜索"""
        if not self.bm25 or not self.corpus:
            return []
        
        # BM25 搜索
        query_tokens = self.tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # 向量搜索（查询与每个文档的相似度）
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            # 如果 embedding 失败，只用 BM25
            vector_scores = np.zeros(len(self.corpus))
        else:
            vector_scores = []
            for doc in self.corpus:
                doc_embedding = self.get_embedding(doc.get("content", "")[:500])  # 限制长度
                if doc_embedding:
                    # 计算余弦相似度
                    similarity = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    vector_scores.append(similarity)
                else:
                    vector_scores.append(0)
            vector_scores = np.array(vector_scores)
        
        # 融合分数
        # 归一化 BM25 分数到 [0, 1]
        if bm25_scores.max() > 0:
            bm25_normalized = bm25_scores / bm25_scores.max()
        else:
            bm25_normalized = bm25_scores
        
        # 归一化向量分数到 [0, 1]（如果存在）
        if vector_scores.max() > 0:
            vector_normalized = (vector_scores - vector_scores.min()) / (vector_scores.max() - vector_scores.min())
        else:
            vector_normalized = vector_scores
        
        # 加权融合
        combined_scores = (
            self.bm25_weight * bm25_normalized + 
            self.vector_weight * vector_normalized
        )
        
        # 获取 top_k 结果
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc = self.corpus[idx]
            results.append({
                "document": doc,
                "bm25_score": float(bm25_scores[idx]),
                "vector_score": float(vector_scores[idx]),
                "combined_score": float(combined_scores[idx]),
                "rank": len(results) + 1
            })
        
        return results

def load_memories_from_files(memory_dir: str) -> List[Dict]:
    """从 memory 目录加载记忆文件"""
    documents = []
    memory_path = Path(memory_dir)
    
    if not memory_path.exists():
        return documents
    
    for md_file in memory_path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        documents.append({
            "id": md_file.stem,
            "content": content,
            "path": str(md_file),
            "title": md_file.name
        })
    
    return documents

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Search for Mem0")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--memory-dir", default="memory", help="Memory directory")
    parser.add_argument("--vector-weight", type=float, default=0.7, help="Vector search weight")
    parser.add_argument("--bm25-weight", type=float, default=0.3, help="BM25 weight")
    
    args = parser.parse_args()
    
    # 加载记忆
    print(f"Loading memories from {args.memory_dir}...")
    documents = load_memories_from_files(args.memory_dir)
    
    if not documents:
        print("No documents found!")
        return
    
    print(f"Loaded {len(documents)} documents")
    
    # 创建搜索器
    searcher = HybridSearch(
        vector_weight=args.vector_weight,
        bm25_weight=args.bm25_weight
    )
    
    # 索引
    print("Indexing...")
    searcher.index_documents(documents)
    
    # 搜索
    print(f"\nSearching for: {args.query}")
    print("-" * 50)
    
    results = searcher.search(args.query, top_k=args.top_k)
    
    for i, result in enumerate(results, 1):
        doc = result["document"]
        print(f"\n{i}. {doc['title']}")
        print(f"   Combined: {result['combined_score']:.3f} | "
              f"BM25: {result['bm25_score']:.3f} | "
              f"Vector: {result['vector_score']:.3f}")
        # 显示前200字符
        preview = doc['content'][:200].replace('\n', ' ')
        print(f"   Preview: {preview}...")

if __name__ == "__main__":
    main()
