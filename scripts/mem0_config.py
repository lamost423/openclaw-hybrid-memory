"""
Mem0 Configuration - 使用 Kimi (Moonshot) API
"""
import os

# Moonshot API Key
MOONSHOT_API_KEY = "sk-kimi-tmq8BLYkmo5Li8i0COdgMERqdgMTMfiwZ79C47lWLN3lRKhG58PQe1IKZWaPbpGb"

MEM0_CONFIG = {
    "vector_store": {
        "provider": "faiss",
        "config": {
            "path": "/Users/danielwu/.openclaw/mem0/production_db",
            "embedding_model_dims": 1024
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
            "model": "qwen2.5:3b",
            "ollama_base_url": "http://localhost:11434",
            "temperature": 0.1,
            "max_tokens": 2000
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
