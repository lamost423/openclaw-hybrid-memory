#!/usr/bin/env python3
"""
Self-Memory Enhanced Search - 完整增强版搜索
集成：混合搜索 + 搜索历史 + 缓存 + 增量更新
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Optional

# 路径设置
workspace = Path.home() / ".openclaw" / "workspace"
venv_path = Path.home() / ".openclaw" / "venv"
if venv_path.exists():
    sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))
sys.path.insert(0, str(workspace / "scripts" / "self-memory"))

from hybrid_search import HybridSearch, load_memories_from_files

def enhanced_search(query: str, top_k: int = 5, use_cache: bool = True, 
                   record_history: bool = True) -> List[Dict]:
    """
    增强版搜索 - 带缓存和历史记录
    """
    start_time = time.time()
    
    # 1. 尝试从缓存获取
    if use_cache:
        try:
            from search_cache import get_search_cache
            cache = get_search_cache()
            cached = cache.get(query)
            if cached:
                print(f"🎯 Cache hit!")
                return cached
        except Exception as e:
            pass
    
    # 2. 执行混合搜索
    memory_dir = workspace / "memory"
    documents = load_memories_from_files(str(memory_dir))
    
    if not documents:
        return []
    
    searcher = HybridSearch(vector_weight=0.7, bm25_weight=0.3)
    searcher.index_documents(documents)
    results = searcher.search(query, top_k=top_k)
    
    # 3. 记录搜索历史
    if record_history:
        try:
            from search_history import record_search
            duration_ms = int((time.time() - start_time) * 1000)
            record_search(query, results, "hybrid", duration_ms)
        except:
            pass
    
    # 4. 存入缓存
    if use_cache:
        try:
            from search_cache import get_search_cache
            cache = get_search_cache()
            cache.set(query, results)
        except:
            pass
    
    return results

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Memory Enhanced Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--no-history", action="store_true", help="Disable history")
    parser.add_argument("--suggestions", action="store_true", help="Show similar queries")
    
    args = parser.parse_args()
    
    # 显示搜索建议
    if args.suggestions:
        try:
            from search_history import get_search_suggestions
            suggestions = get_search_suggestions(args.query)
            if suggestions:
                print("💡 Similar queries:")
                for s in suggestions:
                    print(f"  - {s}")
                print()
        except:
            pass
    
    # 执行搜索
    print(f"🔍 Searching: {args.query}")
    print("-" * 60)
    
    results = enhanced_search(
        args.query,
        top_k=args.top_k,
        use_cache=not args.no_cache,
        record_history=not args.no_history
    )
    
    # 显示结果
    for i, result in enumerate(results, 1):
        doc = result["document"]
        print(f"\n{i}. {doc['title']}")
        print(f"   Score: {result['combined_score']:.3f}")
        preview = doc['content'][:150].replace('\n', ' ')
        print(f"   {preview}...")
    
    print(f"\n✅ Found {len(results)} results")

if __name__ == "__main__":
    main()
