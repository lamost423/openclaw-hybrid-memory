"""
Mem0 Configuration - 修复版 (使用 OpenAI 兼容模式)
OpenRouter 通过 OpenAI 兼容 API 调用
"""
import os

MEM0_CONFIG = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "path": "/Users/danielwu/.openclaw/mem0/faiss_db"
        }
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "mem0password"
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "google/gemini-2.0-flash-001",
            "api_key": "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",
            "openai_base_url": "https://openrouter.ai/api/v1",
            "temperature": 0.1
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "google/gemini-embedding-exp-03-07",
            "api_key": "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",
            "openai_base_url": "https://openrouter.ai/api/v1",
            "embedding_dims": 3072
        }
    }
}
