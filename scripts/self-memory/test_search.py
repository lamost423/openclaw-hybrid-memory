#!/usr/bin/env python3
"""
Test Search Script - 测试混合搜索效果
对比纯 BM25、纯向量、混合搜索的精度
"""

import os
import sys
import json
import pickle
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

# 添加虚拟环境路径
venv_path = Path.home() / ".openclaw" / "venv"
if venv_path.exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))

from rank_bm25 import BM25Okapi


@dataclass
class SearchResult:
    """搜索结果数据类"""
    doc_id: str
    filename: str
    content: str
    score: float
    method: str
    rank: int


class SearchTester:
    """搜索测试器 - 对比不同搜索方法"""
    
    def __init__(self):
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.index_dir = self.workspace / "config" / "self-memory" / "index"
        self.ollama_url = "http://localhost:11434/api/embeddings"
        
        # 加载的数据
        self.bm25 = None
        self.tokenized_corpus = []
        self.embeddings = None
        self.documents = []
        self.doc_map = {}  # id -> index
        
    def load_index(self) -> bool:
        """加载索引文件"""
        print("📂 Loading index files...")
        
        # 加载 BM25
        bm25_path = self.index_dir / "bm25_index.pkl"
        if not bm25_path.exists():
            print(f"❌ BM25 index not found: {bm25_path}")
            print("   Run: python scripts/self-memory/build_index.py")
            return False
        
        with open(bm25_path, "rb") as f:
            bm25_data = pickle.load(f)
            self.bm25 = bm25_data["bm25"]
            self.tokenized_corpus = bm25_data["tokenized_corpus"]
        print(f"  ✓ Loaded BM25 index")
        
        # 加载向量索引
        vector_path = self.index_dir / "vector_index.npy"
        if not vector_path.exists():
            print(f"❌ Vector index not found: {vector_path}")
            return False
        
        self.embeddings = np.load(vector_path)
        print(f"  ✓ Loaded vector index: {self.embeddings.shape}")
        
        # 加载文档
        docs_path = self.index_dir / "documents.json"
        with open(docs_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
        
        # 构建文档映射
        for i, doc in enumerate(self.documents):
            self.doc_map[doc["id"]] = i
        
        print(f"  ✓ Loaded {len(self.documents)} documents")
        return True
    
    def tokenize(self, text: str) -> List[str]:
        """分词"""
        import re
        tokens = re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+|\d+', text.lower())
        return tokens
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本 embedding"""
        import requests
        try:
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
    
    def search_bm25(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """纯 BM25 搜索"""
        query_tokens = self.tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取 top_k 索引
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            doc = self.documents[idx]
            results.append(SearchResult(
                doc_id=doc["id"],
                filename=doc["filename"],
                content=doc["content"][:500],
                score=float(scores[idx]),
                method="BM25",
                rank=rank
            ))
        return results
    
    def search_vector(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """纯向量搜索"""
        query_embedding = self.get_embedding(query)
        
        if not query_embedding:
            return []
        
        query_vec = np.array(query_embedding)
        
        # 计算余弦相似度
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec)
        norms = np.where(norms == 0, 1, norms)  # 避免除零
        similarities = np.dot(self.embeddings, query_vec) / norms
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            doc = self.documents[idx]
            results.append(SearchResult(
                doc_id=doc["id"],
                filename=doc["filename"],
                content=doc["content"][:500],
                score=float(similarities[idx]),
                method="Vector",
                rank=rank
            ))
        return results
    
    def search_hybrid(self, query: str, top_k: int = 5, 
                      vector_weight: float = 0.7, bm25_weight: float = 0.3) -> List[SearchResult]:
        """混合搜索"""
        # BM25 分数
        query_tokens = self.tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # 向量分数
        query_embedding = self.get_embedding(query)
        if query_embedding:
            query_vec = np.array(query_embedding)
            norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec)
            norms = np.where(norms == 0, 1, norms)
            vector_scores = np.dot(self.embeddings, query_vec) / norms
        else:
            vector_scores = np.zeros(len(self.documents))
        
        # 归一化
        if bm25_scores.max() > 0:
            bm25_norm = bm25_scores / bm25_scores.max()
        else:
            bm25_norm = bm25_scores
        
        if vector_scores.max() > vector_scores.min():
            vector_norm = (vector_scores - vector_scores.min()) / (vector_scores.max() - vector_scores.min())
        else:
            vector_norm = vector_scores
        
        # 融合
        combined = bm25_weight * bm25_norm + vector_weight * vector_norm
        
        top_indices = np.argsort(combined)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            doc = self.documents[idx]
            results.append(SearchResult(
                doc_id=doc["id"],
                filename=doc["filename"],
                content=doc["content"][:500],
                score=float(combined[idx]),
                method="Hybrid",
                rank=rank
            ))
        return results
    
    def calculate_precision(self, results: List[SearchResult], relevant_docs: List[str]) -> float:
        """计算 Precision@K"""
        if not results:
            return 0.0
        
        hits = sum(1 for r in results if r.doc_id in relevant_docs)
        return hits / len(results)
    
    def calculate_recall(self, results: List[SearchResult], relevant_docs: List[str]) -> float:
        """计算 Recall@K"""
        if not relevant_docs:
            return 0.0
        
        found = set(r.doc_id for r in results if r.doc_id in relevant_docs)
        return len(found) / len(relevant_docs)
    
    def calculate_mrr(self, results: List[SearchResult], relevant_docs: List[str]) -> float:
        """计算 MRR (Mean Reciprocal Rank)"""
        for i, r in enumerate(results):
            if r.doc_id in relevant_docs:
                return 1.0 / (i + 1)
        return 0.0
    
    def run_test(self, test_cases: List[Dict]) -> Dict:
        """运行测试用例"""
        print("\n" + "=" * 70)
        print("SEARCH TEST SUITE")
        print("=" * 70)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_cases": [],
            "summary": {}
        }
        
        method_stats = {
            "BM25": {"precisions": [], "recalls": [], "mrrs": [], "times": []},
            "Vector": {"precisions": [], "recalls": [], "mrrs": [], "times": []},
            "Hybrid": {"precisions": [], "recalls": [], "mrrs": [], "times": []}
        }
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            relevant = test_case["relevant_docs"]
            description = test_case.get("description", "")
            
            print(f"\n📌 Test {i}/{len(test_cases)}: {query}")
            if description:
                print(f"   Description: {description}")
            print(f"   Relevant docs: {relevant}")
            print("-" * 50)
            
            test_result = {
                "query": query,
                "description": description,
                "relevant_docs": relevant,
                "methods": {}
            }
            
            # 测试每种方法
            for method_name, search_func in [
                ("BM25", lambda: self.search_bm25(query, top_k=5)),
                ("Vector", lambda: self.search_vector(query, top_k=5)),
                ("Hybrid", lambda: self.search_hybrid(query, top_k=5, vector_weight=0.7, bm25_weight=0.3))
            ]:
                start_time = time.time()
                method_results = search_func()
                elapsed = time.time() - start_time
                
                precision = self.calculate_precision(method_results, relevant)
                recall = self.calculate_recall(method_results, relevant)
                mrr = self.calculate_mrr(method_results, relevant)
                
                method_stats[method_name]["precisions"].append(precision)
                method_stats[method_name]["recalls"].append(recall)
                method_stats[method_name]["mrrs"].append(mrr)
                method_stats[method_name]["times"].append(elapsed)
                
                print(f"\n   {method_name}:")
                print(f"     Time: {elapsed:.3f}s | P@5: {precision:.2f} | R@5: {recall:.2f} | MRR: {mrr:.3f}")
                for r in method_results[:3]:
                    match = "✓" if r.doc_id in relevant else " "
                    print(f"     [{match}] {r.filename} (score: {r.score:.3f})")
                
                test_result["methods"][method_name] = {
                    "time": elapsed,
                    "precision": precision,
                    "recall": recall,
                    "mrr": mrr,
                    "results": [{"id": r.doc_id, "score": r.score} for r in method_results]
                }
            
            results["test_cases"].append(test_result)
        
        # 计算汇总统计
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        for method_name, stats in method_stats.items():
            avg_precision = np.mean(stats["precisions"])
            avg_recall = np.mean(stats["recalls"])
            avg_mrr = np.mean(stats["mrrs"])
            avg_time = np.mean(stats["times"])
            
            results["summary"][method_name] = {
                "avg_precision": float(avg_precision),
                "avg_recall": float(avg_recall),
                "avg_mrr": float(avg_mrr),
                "avg_time": float(avg_time)
            }
            
            print(f"\n{method_name}:")
            print(f"  Average Precision@5: {avg_precision:.3f}")
            print(f"  Average Recall@5:    {avg_recall:.3f}")
            print(f"  Average MRR:         {avg_mrr:.3f}")
            print(f"  Average Time:        {avg_time:.3f}s")
        
        return results
    
    def save_report(self, results: Dict, output_path: str = None):
        """保存测试报告"""
        if not output_path:
            output_path = self.workspace / "memory" / f"search_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        output_path = Path(output_path)
        
        lines = [
            "# Self-Memory Search Test Report\n",
            f"**Generated:** {results['timestamp']}\n",
            f"**Documents Indexed:** {len(self.documents)}\n\n",
            "## Summary\n\n",
            "| Method | Precision@5 | Recall@5 | MRR | Avg Time |\n",
            "|--------|-------------|----------|-----|----------|\n"
        ]
        
        for method, stats in results["summary"].items():
            lines.append(
                f"| {method} | {stats['avg_precision']:.3f} | "
                f"{stats['avg_recall']:.3f} | {stats['avg_mrr']:.3f} | "
                f"{stats['avg_time']:.3f}s |\n"
            )
        
        lines.extend(["\n## Test Cases\n"])
        
        for tc in results["test_cases"]:
            lines.extend([
                f"\n### {tc['query']}\n",
                f"Description: {tc.get('description', 'N/A')}\n",
                f"Relevant docs: {', '.join(tc['relevant_docs'])}\n\n"
            ])
            
            lines.append("| Method | P@5 | R@5 | MRR | Time |\n")
            lines.append("|--------|-----|-----|-----|------|\n")
            
            for method, stats in tc["methods"].items():
                lines.append(
                    f"| {method} | {stats['precision']:.2f} | "
                    f"{stats['recall']:.2f} | {stats['mrr']:.3f} | "
                    f"{stats['time']:.3f}s |\n"
                )
        
        output_path.write_text("".join(lines), encoding="utf-8")
        print(f"\n📝 Report saved: {output_path}")


def get_test_cases() -> List[Dict]:
    """定义测试用例"""
    return [
        {
            "query": "Reddit 推广策略",
            "description": "查找 Reddit 相关的推广内容",
            "relevant_docs": ["2026-02-26"]
        },
        {
            "query": "memory system architecture",
            "description": "英文查询记忆系统架构",
            "relevant_docs": ["2026-02-27"]
        },
        {
            "query": "heartbeat configuration",
            "description": "心跳配置相关",
            "relevant_docs": ["2026-02-28"]
        },
        {
            "query": "Mem0 vector store",
            "description": "Mem0 向量存储配置",
            "relevant_docs": ["2026-02-27"]
        },
        {
            "query": "自媒体运营",
            "description": "中文自媒体相关内容",
            "relevant_docs": ["2026-02-25"]
        }
    ]


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Self-Memory Search")
    parser.add_argument("--output", help="Output report path")
    parser.add_argument("--query", help="Run single query test")
    
    args = parser.parse_args()
    
    tester = SearchTester()
    
    if not tester.load_index():
        print("\n❌ Failed to load index. Please build it first.")
        sys.exit(1)
    
    if args.query:
        # 单查询测试
        print(f"\n🔍 Testing query: {args.query}\n")
        
        print("BM25 Results:")
        for r in tester.search_bm25(args.query, top_k=3):
            print(f"  {r.rank}. {r.filename} (score: {r.score:.3f})")
        
        print("\nVector Results:")
        for r in tester.search_vector(args.query, top_k=3):
            print(f"  {r.rank}. {r.filename} (score: {r.score:.3f})")
        
        print("\nHybrid Results:")
        for r in tester.search_hybrid(args.query, top_k=3):
            print(f"  {r.rank}. {r.filename} (score: {r.score:.3f})")
    else:
        # 完整测试套件
        test_cases = get_test_cases()
        results = tester.run_test(test_cases)
        tester.save_report(results, args.output)


if __name__ == "__main__":
    main()
