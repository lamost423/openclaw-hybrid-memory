#!/usr/bin/env python3
"""
Mem0 Bridge Enhanced - 增强版 Mem0 桥接脚本
结合 Self-Memory 混合搜索 + Mem0 搜索结果，合并去重，优先混合搜索
集成搜索历史记录和缓存功能
"""

import os
import sys
import json
import pickle
import argparse
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 添加虚拟环境路径
venv_path = Path.home() / ".openclaw" / "venv"
if venv_path.exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from mem0_config import MEM0_CONFIG
except ImportError:
    MEM0_CONFIG = {}
from rank_bm25 import BM25Okapi

# 导入增强模块
HISTORY_ENABLED = False
CACHE_ENABLED = False

# 尝试导入搜索历史模块
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from search_history import record_search, get_search_suggestions
    HISTORY_ENABLED = True
except ImportError as e:
    pass

# 尝试导入缓存模块
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from search_cache import get_search_cache
    CACHE_ENABLED = True
except ImportError as e:
    pass


@dataclass
class UnifiedResult:
    """统一搜索结果格式"""
    source: str  # "self-memory" 或 "mem0"
    id: str
    content: str
    score: float
    metadata: Dict
    rank: int = 0


class SelfMemorySearcher:
    """Self-Memory 混合搜索器"""
    
    def __init__(self):
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.index_dir = self.workspace / "config" / "self-memory" / "index"
        self.ollama_url = "http://localhost:11434/api/embeddings"
        
        self.bm25 = None
        self.tokenized_corpus = []
        self.embeddings = None
        self.documents = []
        self.loaded = False
    
    def load_index(self) -> bool:
        """加载索引"""
        if self.loaded:
            return True
        
        try:
            # 加载文档
            docs_path = self.index_dir / "documents.json"
            with open(docs_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            
            # 从文档重建 tokenized_corpus
            self.tokenized_corpus = [self.tokenize(d["content"]) for d in self.documents]
            
            # 加载 BM25（如果不存在则重建）
            bm25_path = self.index_dir / "bm25_index.pkl"
            if bm25_path.exists():
                with open(bm25_path, "rb") as f:
                    loaded_bm25 = pickle.load(f)
                    # 验证加载的对象类型
                    if hasattr(loaded_bm25, 'get_scores'):
                        self.bm25 = loaded_bm25
                    else:
                        print("⚠️  BM25 index corrupted, rebuilding...")
                        self.bm25 = BM25Okapi(self.tokenized_corpus)
                        self._save_bm25()
            else:
                print("⚠️  BM25 index not found, rebuilding...")
                self.bm25 = BM25Okapi(self.tokenized_corpus)
                self._save_bm25()
            
            # 加载向量索引
            vector_path = self.index_dir / "vector_index.npy"
            self.embeddings = np.load(vector_path)
            
            self.loaded = True
            return True
        except Exception as e:
            print(f"⚠️  Failed to load self-memory index: {e}")
            return False
    
    def _save_bm25(self):
        """保存 BM25 索引"""
        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            bm25_path = self.index_dir / "bm25_index.pkl"
            with open(bm25_path, "wb") as f:
                pickle.dump(self.bm25, f)
        except Exception as e:
            print(f"⚠️  Failed to save BM25 index: {e}")
    
    def tokenize(self, text: str) -> List[str]:
        """分词"""
        import re
        tokens = re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+|\d+', text.lower())
        return tokens
    
    def get_embedding(self, text: str) -> List[float]:
        """获取 embedding"""
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
            return []
    
    def search(self, query: str, top_k: int = 5, 
               vector_weight: float = 0.7, bm25_weight: float = 0.3) -> List[UnifiedResult]:
        """执行混合搜索"""
        if not self.load_index():
            return []
        
        # BM25 搜索
        query_tokens = self.tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # 向量搜索
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
            results.append(UnifiedResult(
                source="self-memory",
                id=doc["id"],
                content=doc["content"],
                score=float(combined[idx]),
                metadata={
                    "filename": doc.get("filename", doc["id"]),
                    "path": doc.get("path", ""),
                    "bm25_score": float(bm25_scores[idx]),
                    "vector_score": float(vector_scores[idx])
                },
                rank=rank
            ))
        
        return results


class Mem0Searcher:
    """Mem0 搜索器"""
    
    def __init__(self):
        try:
            from mem0 import Memory
            self.memory = Memory.from_config(MEM0_CONFIG)
            self.available = True
        except Exception as e:
            self.available = False
            self.memory = None
    
    def search(self, query: str, user_id: str = "daniel", limit: int = 5) -> List[UnifiedResult]:
        """搜索 Mem0"""
        if not self.available:
            return []
        
        try:
            results = self.memory.search(query, user_id=user_id, limit=limit)
            items = results.get("results", [])
            
            unified = []
            for i, item in enumerate(items, 1):
                unified.append(UnifiedResult(
                    source="mem0",
                    id=item.get("id", f"mem0_{i}"),
                    content=item.get("memory", ""),
                    score=item.get("score", 0.0),
                    metadata={
                        "metadata": item.get("metadata", {}),
                        "created_at": item.get("created_at", "")
                    },
                    rank=i
                ))
            return unified
        except Exception as e:
            return []
    
    def add(self, text: str, user_id: str = "daniel") -> Dict:
        """添加记忆到 Mem0"""
        if not self.available:
            return {"error": "Mem0 not available"}
        
        try:
            result = self.memory.add(text, user_id=user_id)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_all(self, user_id: str = "daniel") -> List[UnifiedResult]:
        """获取所有 Mem0 记忆"""
        if not self.available:
            return []
        
        try:
            results = self.memory.get_all(user_id=user_id)
            items = results.get("results", [])
            
            unified = []
            for i, item in enumerate(items, 1):
                unified.append(UnifiedResult(
                    source="mem0",
                    id=item.get("id", f"mem0_{i}"),
                    content=item.get("memory", ""),
                    score=1.0,
                    metadata=item.get("metadata", {}),
                    rank=i
                ))
            return unified
        except Exception as e:
            return []


class EnhancedSearchEngine:
    """增强搜索引擎 - 合并 Self-Memory 和 Mem0 结果"""
    
    def __init__(self):
        self.self_memory = SelfMemorySearcher()
        self.mem0 = Mem0Searcher()
    
    def deduplicate_results(self, results: List[UnifiedResult], 
                           threshold: float = 0.85) -> List[UnifiedResult]:
        """基于内容相似度去重"""
        if not results:
            return []
        
        unique_results = []
        
        for result in results:
            is_duplicate = False
            
            for existing in unique_results:
                similarity = self._content_similarity(result.content, existing.content)
                if similarity >= threshold:
                    if result.score > existing.score:
                        existing.content = result.content
                        existing.score = result.score
                        existing.metadata.update(result.metadata)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def _content_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度（简单 Jaccard）"""
        import re
        
        def get_tokens(text):
            return set(re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+|\d+', text.lower()))
        
        tokens1 = get_tokens(text1)
        tokens2 = get_tokens(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def search(self, query: str, user_id: str = "daniel", 
               top_k: int = 5, self_memory_ratio: float = 0.6,
               use_cache: bool = True) -> Tuple[List[UnifiedResult], Dict]:
        """
        执行增强搜索
        
        Returns:
            (结果列表, 元数据)
        """
        start_time = time.time()
        meta = {"cache_hit": False, "duration_ms": 0, "sources": []}
        
        # 检查缓存
        if use_cache and CACHE_ENABLED:
            cache = get_search_cache()
            cached = cache.get(query)
            if cached is not None:
                meta["cache_hit"] = True
                meta["duration_ms"] = int((time.time() - start_time) * 1000)
                meta["sources"] = [r.get("source", "unknown") for r in cached]
                return [UnifiedResult(**r) for r in cached], meta
        
        # 计算分别从两个来源获取的数量
        self_memory_k = max(1, int(top_k * self_memory_ratio))
        mem0_k = max(1, int(top_k * (1 - self_memory_ratio)))
        
        # 执行搜索
        self_results = self.self_memory.search(query, top_k=self_memory_k * 2)
        mem0_results = self.mem0.search(query, user_id=user_id, limit=mem0_k * 2)
        
        # 标记来源并调整分数范围
        for r in self_results:
            r.score = r.score * self_memory_ratio
        
        for r in mem0_results:
            r.score = r.score * (1 - self_memory_ratio)
        
        # 合并结果
        all_results = self_results + mem0_results
        
        # 去重
        deduplicated = self.deduplicate_results(all_results)
        
        # 按分数排序并截取 top_k
        deduplicated.sort(key=lambda x: x.score, reverse=True)
        final_results = deduplicated[:top_k]
        
        # 重新设置 rank
        for i, r in enumerate(final_results, 1):
            r.rank = i
        
        duration_ms = int((time.time() - start_time) * 1000)
        meta["duration_ms"] = duration_ms
        meta["sources"] = list(set([r.source for r in final_results]))
        
        # 存入缓存
        if use_cache and CACHE_ENABLED:
            cache = get_search_cache()
            cache.set(query, [{
                "source": r.source,
                "id": r.id,
                "content": r.content,
                "score": r.score,
                "metadata": r.metadata,
                "rank": r.rank
            } for r in final_results])
        
        return final_results, meta
    
    def format_results(self, results: List[UnifiedResult], 
                       show_metadata: bool = False) -> str:
        """格式化搜索结果为字符串"""
        if not results:
            return "No results found."
        
        lines = [f"Found {len(results)} results:\n"]
        
        for r in results:
            source_icon = "📝" if r.source == "self-memory" else "🧠"
            lines.append(f"{source_icon} [{r.rank}] ({r.score:.3f}) {r.id}")
            
            content = r.content[:200].replace("\n", " ")
            lines.append(f"   {content}...")
            
            if show_metadata and r.metadata:
                lines.append(f"   Metadata: {json.dumps(r.metadata, ensure_ascii=False)[:100]}")
            
            lines.append("")
        
        return "\n".join(lines)


def cmd_search(args):
    """搜索命令 - 集成历史和缓存"""
    engine = EnhancedSearchEngine()
    
    # 显示相似查询建议
    if HISTORY_ENABLED:
        suggestions = get_search_suggestions(args.query, limit=3)
        if suggestions:
            print(f"💡 Similar past queries: {', '.join(suggestions[:3])}\n")
    
    start_time = time.time()
    results, meta = engine.search(
        query=args.query,
        user_id=args.user,
        top_k=args.limit,
        self_memory_ratio=args.self_ratio,
        use_cache=not args.no_cache
    )
    
    # 显示缓存状态
    if meta.get("cache_hit"):
        print("🎯 Cache hit!\n")
    
    print(engine.format_results(results, show_metadata=args.verbose))
    print(f"⏱️  Search took {meta['duration_ms']}ms")
    
    # 记录搜索历史
    if HISTORY_ENABLED:
        try:
            record_id = record_search(
                query=args.query,
                results=[{
                    "source": r.source,
                    "id": r.id,
                    "content": r.content[:500],
                    "score": r.score
                } for r in results],
                search_type="enhanced",
                duration_ms=meta["duration_ms"]
            )
            if args.verbose:
                print(f"📝 Recorded as: {record_id}")
        except Exception as e:
            pass


def cmd_add(args):
    """添加记忆命令"""
    engine = EnhancedSearchEngine()
    result = engine.mem0.add(args.text, user_id=args.user)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        extracted = len(result.get("results", []))
        print(f"✅ Added to Mem0, extracted {extracted} facts")
        for r in result.get("results", []):
            print(f"  • {r.get('memory', '')[:100]}")


def cmd_list(args):
    """列出所有 Mem0 记忆"""
    engine = EnhancedSearchEngine()
    results = engine.mem0.get_all(user_id=args.user)
    
    if not results:
        print("No memories found in Mem0.")
        return
    
    print(f"📋 Total {len(results)} memories in Mem0:\n")
    for r in results:
        print(f"  [{r.rank}] {r.content[:120]}")


def cmd_export(args):
    """导出 Mem0 记忆"""
    engine = EnhancedSearchEngine()
    results = engine.mem0.get_all(user_id=args.user)
    
    lines = ["# Mem0 Memory Export\n"]
    for r in results:
        lines.append(f"- {r.content}")
    
    output = args.output or "MEMORY_BACKUP.md"
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ Exported {len(results)} memories to {output}")


def cmd_self_search(args):
    """仅搜索 Self-Memory"""
    searcher = SelfMemorySearcher()
    results = searcher.search(args.query, top_k=args.limit)
    
    if not results:
        print("No results found in self-memory.")
        return
    
    print(f"📝 Self-Memory Results ({len(results)} found):\n")
    for r in results:
        print(f"  [{r.rank}] ({r.score:.3f}) {r.metadata.get('filename', r.id)}")
        content = r.content[:200].replace("\n", " ")
        print(f"      {content}...\n")


def cmd_compare(args):
    """对比 Self-Memory 和 Mem0 搜索结果"""
    engine = EnhancedSearchEngine()
    
    print(f"🔍 Comparing search methods for: {args.query}\n")
    
    # Self-Memory 搜索
    print("=" * 50)
    print("Self-Memory (Hybrid Search):")
    print("=" * 50)
    self_results = engine.self_memory.search(args.query, top_k=args.limit)
    for r in self_results:
        print(f"  [{r.rank}] ({r.score:.3f}) {r.metadata.get('filename', r.id)}")
        print(f"      {r.content[:150].replace(chr(10), ' ')}...")
    
    # Mem0 搜索
    print("\n" + "=" * 50)
    print("Mem0 (Vector Search):")
    print("=" * 50)
    mem0_results = engine.mem0.search(args.query, user_id=args.user, limit=args.limit)
    for r in mem0_results:
        print(f"  [{r.rank}] ({r.score:.3f}) {r.id}")
        print(f"      {r.content[:150].replace(chr(10), ' ')}...")
    
    # 增强搜索
    print("\n" + "=" * 50)
    print("Enhanced (Merged):")
    print("=" * 50)
    enhanced_results, meta = engine.search(args.query, user_id=args.user, top_k=args.limit)
    for r in enhanced_results:
        icon = "📝" if r.source == "self-memory" else "🧠"
        print(f"  {icon} [{r.rank}] ({r.score:.3f}) {r.id}")
        print(f"      {r.content[:150].replace(chr(10), ' ')}...")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Mem0 Bridge Enhanced - Hybrid Self-Memory + Mem0 Search"
    )
    parser.add_argument("--user", default="daniel", help="User ID")
    
    sub = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    p_search = sub.add_parser("search", help="Search both Self-Memory and Mem0")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=5, help="Number of results")
    p_search.add_argument("--self-ratio", type=float, default=0.6, 
                          help="Self-Memory result ratio (0-1)")
    p_search.add_argument("--verbose", action="store_true", help="Show metadata")
    p_search.add_argument("--no-cache", action="store_true", help="Disable cache")
    
    # Add command
    p_add = sub.add_parser("add", help="Add memory to Mem0")
    p_add.add_argument("text", help="Memory content")
    
    # List command
    p_list = sub.add_parser("list", help="List all Mem0 memories")
    
    # Export command
    p_export = sub.add_parser("export", help="Export Mem0 memories")
    p_export.add_argument("--output", help="Output file path")
    
    # Self-memory only search
    p_self = sub.add_parser("self-search", help="Search only Self-Memory")
    p_self.add_argument("query", help="Search query")
    p_self.add_argument("--limit", type=int, default=5, help="Number of results")
    
    # Compare command
    p_compare = sub.add_parser("compare", help="Compare search methods")
    p_compare.add_argument("query", help="Search query")
    p_compare.add_argument("--limit", type=int, default=3, help="Number of results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "search": cmd_search,
        "add": cmd_add,
        "list": cmd_list,
        "export": cmd_export,
        "self-search": cmd_self_search,
        "compare": cmd_compare
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
