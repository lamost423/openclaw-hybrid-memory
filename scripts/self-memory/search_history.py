#!/usr/bin/env python3
"""
Search History & Feedback - 搜索历史记录与反馈系统
记录搜索查询、结果和用户反馈，用于持续优化
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class SearchRecord:
    """搜索记录"""
    query: str
    timestamp: str
    results: List[Dict]
    search_type: str  # "self-memory", "mem0", "hybrid"
    duration_ms: int
    result_count: int
    feedback: Optional[str] = None  # "helpful", "not_helpful", "partial"
    feedback_comment: Optional[str] = None

def get_workspace():
    return Path.home() / ".openclaw" / "workspace"

class SearchHistoryManager:
    """搜索历史管理器"""
    
    def __init__(self):
        self.workspace = get_workspace()
        self.history_dir = self.workspace / "config" / "self-memory" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / "search_history.json"
        self.feedback_file = self.history_dir / "feedback.json"
        self.stats_file = self.history_dir / "stats.json"
    
    def add_record(self, query: str, results: List[Dict], search_type: str = "hybrid", 
                   duration_ms: int = 0) -> str:
        """添加搜索记录"""
        record = SearchRecord(
            query=query,
            timestamp=datetime.now().isoformat(),
            results=results[:5],  # 只保存前5个结果
            search_type=search_type,
            duration_ms=duration_ms,
            result_count=len(results)
        )
        
        # 生成记录ID
        record_id = hashlib.md5(f"{query}{record.timestamp}".encode()).hexdigest()[:12]
        
        # 加载现有历史
        history = self._load_history()
        history.append({"id": record_id, **asdict(record)})
        
        # 只保留最近100条
        history = history[-100:]
        
        # 保存
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        # 更新统计
        self._update_stats(query)
        
        return record_id
    
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def add_feedback(self, record_id: str, feedback: str, comment: str = ""):
        """添加用户反馈"""
        feedbacks = []
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            except:
                pass
        
        feedbacks.append({
            "record_id": record_id,
            "feedback": feedback,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        })
        
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedbacks, f, indent=2, ensure_ascii=False)
        
        # 更新历史记录中的反馈
        self._update_record_feedback(record_id, feedback, comment)
    
    def _update_record_feedback(self, record_id: str, feedback: str, comment: str):
        """更新记录中的反馈"""
        history = self._load_history()
        for record in history:
            if record.get("id") == record_id:
                record["feedback"] = feedback
                record["feedback_comment"] = comment
                break
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def _update_stats(self, query: str):
        """更新搜索统计"""
        stats = self._load_stats()
        
        # 更新热门查询
        query_key = query.lower().strip()
        if query_key not in stats["top_queries"]:
            stats["top_queries"][query_key] = 0
        stats["top_queries"][query_key] += 1
        
        # 更新时间分布
        hour = datetime.now().hour
        stats["hourly_distribution"][str(hour)] = stats["hourly_distribution"].get(str(hour), 0) + 1
        
        # 更新总次数
        stats["total_searches"] = stats.get("total_searches", 0) + 1
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def _load_stats(self) -> Dict:
        """加载统计"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "total_searches": 0,
            "top_queries": {},
            "hourly_distribution": {}
        }
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """获取搜索历史"""
        history = self._load_history()
        return history[-limit:][::-1]  # 倒序，最新的在前
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._load_stats()
    
    def get_similar_queries(self, query: str, limit: int = 5) -> List[str]:
        """获取相似的历史查询"""
        history = self._load_history()
        query_lower = query.lower()
        
        # 简单匹配包含相同关键词的查询
        similar = []
        for record in history[::-1]:  # 从最新的开始
            if query_lower in record["query"].lower() or record["query"].lower() in query_lower:
                if record["query"] != query and record["query"] not in similar:
                    similar.append(record["query"])
                    if len(similar) >= limit:
                        break
        
        return similar
    
    def get_top_queries(self, limit: int = 10) -> List[tuple]:
        """获取热门查询"""
        stats = self._load_stats()
        sorted_queries = sorted(
            stats["top_queries"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:limit]
    
    def get_feedback_summary(self) -> Dict:
        """获取反馈汇总"""
        if not self.feedback_file.exists():
            return {"total": 0, "helpful": 0, "not_helpful": 0, "partial": 0}
        
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except:
            return {"total": 0, "helpful": 0, "not_helpful": 0, "partial": 0}
        
        summary = {"total": len(feedbacks), "helpful": 0, "not_helpful": 0, "partial": 0}
        for f in feedbacks:
            key = f.get("feedback", "unknown")
            if key in summary:
                summary[key] += 1
        
        return summary

# 全局实例
_history_manager = None

def get_history_manager() -> SearchHistoryManager:
    """获取搜索历史管理器单例"""
    global _history_manager
    if _history_manager is None:
        _history_manager = SearchHistoryManager()
    return _history_manager

def record_search(query: str, results: List[Dict], search_type: str = "hybrid", 
                  duration_ms: int = 0) -> str:
    """记录搜索（便捷函数）"""
    return get_history_manager().add_record(query, results, search_type, duration_ms)

def record_feedback(record_id: str, feedback: str, comment: str = ""):
    """记录反馈（便捷函数）"""
    get_history_manager().add_feedback(record_id, feedback, comment)

def get_search_suggestions(query: str, limit: int = 5) -> List[str]:
    """获取搜索建议"""
    return get_history_manager().get_similar_queries(query, limit)

# CLI 接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Search History & Feedback")
    parser.add_argument("--history", action="store_true", help="Show search history")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--feedback", nargs=3, metavar=("RECORD_ID", "TYPE", "COMMENT"),
                        help="Add feedback (type: helpful/not_helpful/partial)")
    parser.add_argument("--similar", metavar="QUERY", help="Find similar queries")
    parser.add_argument("--limit", type=int, default=20, help="Limit results")
    
    args = parser.parse_args()
    
    manager = get_history_manager()
    
    if args.history:
        history = manager.get_history(args.limit)
        print(f"📜 Search History (last {len(history)}):")
        print("-" * 60)
        for h in history:
            time = h['timestamp'][11:16]
            fb = f" [{h.get('feedback', '?')}]" if h.get('feedback') else ""
            print(f"{time} [{h['search_type']}] {h['query'][:50]}{fb}")
    
    elif args.stats:
        stats = manager.get_stats()
        summary = manager.get_feedback_summary()
        
        print("📊 Search Statistics:")
        print("-" * 60)
        print(f"Total searches: {stats['total_searches']}")
        print(f"\nTop queries:")
        for query, count in manager.get_top_queries(10):
            print(f"  {count}x {query[:40]}")
        
        print(f"\nFeedback summary:")
        print(f"  ✅ Helpful: {summary['helpful']}")
        print(f"  ❌ Not helpful: {summary['not_helpful']}")
        print(f"  ⚠️  Partial: {summary['partial']}")
    
    elif args.feedback:
        record_id, feedback_type, comment = args.feedback
        manager.add_feedback(record_id, feedback_type, comment)
        print(f"✅ Feedback recorded: {feedback_type}")
    
    elif args.similar:
        similar = manager.get_similar_queries(args.similar, args.limit)
        print(f"🔍 Similar queries to '{args.similar}':")
        for s in similar:
            print(f"  - {s}")
    
    else:
        parser.print_help()
