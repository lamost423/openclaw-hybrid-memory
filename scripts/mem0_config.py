"""
Mem0 Configuration - 本地版 (使用 Ollama)
完全本地运行，不依赖外部 API
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
        "provider": "ollama",
        "config": {
            "model": "gemma2:2b",
            "temperature": 0.1,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434"
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large",
            "ollama_base_url": "http://localhost:11434",
            "embedding_dims": 1024
        }
    }
}
