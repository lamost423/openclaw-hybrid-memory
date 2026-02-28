#!/usr/bin/env python3
"""
Search Result Cache - 搜索结果缓存系统
缓存热门查询结果，加速响应
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class CacheEntry:
    """缓存条目"""
    query_hash: str
    query: str
    results: List[Dict]
    timestamp: float
    hit_count: int
    last_accessed: float

def get_workspace():
    return Path.home() / ".openclaw" / "workspace"

class SearchCache:
    """搜索结果缓存"""
    
    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        self.workspace = get_workspace()
        self.cache_dir = self.workspace / "config" / "self-memory" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / "search_cache.json"
        self.stats_file = self.cache_dir / "cache_stats.json"
        
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        
        self._cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        entry = CacheEntry(**item)
                        # 检查是否过期
                        if time.time() - entry.timestamp < self.ttl_seconds:
                            self._cache[entry.query_hash] = entry
                        else:
                            self._cache[entry.query_hash] = entry
            except:
                pass
    
    def _save_cache(self):
        """保存缓存"""
        # 清理过期条目
        current_time = time.time()
        expired = [
            k for k, v in self._cache.items()
            if current_time - v.timestamp > self.ttl_seconds
        ]
        for k in expired:
            del self._cache[k]
        
        # 如果超出大小限制，移除最少使用的
        if len(self._cache) > self.max_size:
            # 按访问时间和命中次数排序
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: (x[1].hit_count, x[1].last_accessed),
                reverse=True
            )
            # 保留前 max_size 个
            self._cache = dict(sorted_items[:self.max_size])
        
        # 保存
        data = [asdict(v) for v in self._cache.values()]
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _compute_hash(self, query: str) -> str:
        """计算查询哈希"""
        # 归一化查询：小写、去空格
        normalized = ' '.join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def get(self, query: str) -> Optional[List[Dict]]:
        """获取缓存结果"""
        query_hash = self._compute_hash(query)
        
        if query_hash in self._cache:
            entry = self._cache[query_hash]
            
            # 检查是否过期
            if time.time() - entry.timestamp > self.ttl_seconds:
                del self._cache[query_hash]
                self._update_stats(miss=True)
                return None
            
            # 更新访问信息
            entry.hit_count += 1
            entry.last_accessed = time.time()
            
            self._update_stats(hit=True)
            return entry.results
        
        self._update_stats(miss=True)
        return None
    
    def set(self, query: str, results: List[Dict]):
        """设置缓存"""
        query_hash = self._compute_hash(query)
        
        entry = CacheEntry(
            query_hash=query_hash,
            query=query,
            results=results,
            timestamp=time.time(),
            hit_count=1,
            last_accessed=time.time()
        )
        
        self._cache[query_hash] = entry
        self._save_cache()
        self._update_stats(add=True)
    
    def _update_stats(self, hit: bool = False, miss: bool = False, add: bool = False):
        """更新统计"""
        stats = self._load_stats()
        
        if hit:
            stats["hits"] = stats.get("hits", 0) + 1
        if miss:
            stats["misses"] = stats.get("misses", 0) + 1
        if add:
            stats["adds"] = stats.get("adds", 0) + 1
        
        stats["total_queries"] = stats.get("total_queries", 0) + (1 if hit or miss else 0)
        stats["cache_size"] = len(self._cache)
        
        # 计算命中率
        total = stats.get("hits", 0) + stats.get("misses", 0)
        if total > 0:
            stats["hit_rate"] = stats["hits"] / total
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    def _load_stats(self) -> Dict:
        """加载统计"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"hits": 0, "misses": 0, "adds": 0, "total_queries": 0, "hit_rate": 0, "cache_size": 0}
    
    def invalidate(self, query: str = None):
        """使缓存失效"""
        if query:
            query_hash = self._compute_hash(query)
            if query_hash in self._cache:
                del self._cache[query_hash]
        else:
            # 清空所有缓存
            self._cache.clear()
        
        self._save_cache()
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        stats = self._load_stats()
        stats["current_cache_size"] = len(self._cache)
        stats["max_cache_size"] = self.max_size
        stats["ttl_hours"] = self.ttl_seconds / 3600
        return stats
    
    def get_popular_queries(self, limit: int = 10) -> List[tuple]:
        """获取热门查询"""
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1].hit_count,
            reverse=True
        )
        
        return [
            (item.query, item.hit_count)
            for _, item in sorted_items[:limit]
        ]
    
    def clear_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired = [
            k for k, v in self._cache.items()
            if current_time - v.timestamp > self.ttl_seconds
        ]
        
        for k in expired:
            del self._cache[k]
        
        if expired:
            self._save_cache()
        
        return len(expired)

# 全局缓存实例
_search_cache = None

def get_search_cache() -> SearchCache:
    """获取搜索缓存单例"""
    global _search_cache
    if _search_cache is None:
        _search_cache = SearchCache()
    return _search_cache

def cached_search(query: str, search_func, *args, **kwargs) -> List[Dict]:
    """
    带缓存的搜索
    用法:
        results = cached_search("query", hybrid_search, "query", top_k=5)
    """
    cache = get_search_cache()
    
    # 尝试从缓存获取
    cached_results = cache.get(query)
    if cached_results is not None:
        print(f"🎯 Cache hit for: {query[:30]}...")
        return cached_results
    
    # 执行搜索
    results = search_func(*args, **kwargs)
    
    # 存入缓存
    cache.set(query, results)
    
    return results

# CLI 接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Search Result Cache")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--clear", action="store_true", help="Clear all cache")
    parser.add_argument("--clear-expired", action="store_true", help="Clear expired entries")
    parser.add_argument("--popular", action="store_true", help="Show popular queries")
    parser.add_argument("--invalidate", metavar="QUERY", help="Invalidate specific query")
    
    args = parser.parse_args()
    
    cache = get_search_cache()
    
    if args.stats:
        stats = cache.get_stats()
        print("📊 Cache Statistics:")
        print("-" * 60)
        print(f"Total queries: {stats['total_queries']}")
        print(f"Cache hits: {stats['hits']}")
        print(f"Cache misses: {stats['misses']}")
        print(f"Hit rate: {stats['hit_rate']:.1%}")
        print(f"Current size: {stats['current_cache_size']} / {stats['max_cache_size']}")
        print(f"TTL: {stats['ttl_hours']:.0f} hours")
    
    elif args.clear:
        cache.invalidate()
        print("✅ Cache cleared")
    
    elif args.clear_expired:
        count = cache.clear_expired()
        print(f"✅ Cleared {count} expired entries")
    
    elif args.popular:
        popular = cache.get_popular_queries(10)
        print("🔥 Popular Queries:")
        for query, hits in popular:
            print(f"  {hits}x {query[:50]}")
    
    elif args.invalidate:
        cache.invalidate(args.invalidate)
        print(f"✅ Invalidated cache for: {args.invalidate}")
    
    else:
        parser.print_help()
