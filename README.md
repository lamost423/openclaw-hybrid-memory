# Hybrid Agent Memory System

> A production-ready hybrid memory system combining BM25 keyword search, vector semantic search, and intelligent caching for AI agents.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Why Hybrid Memory?

Traditional AI memory systems force you to choose between **speed** and **accuracy**. This hybrid architecture gives you **both**.

| Approach | Keyword Match | Semantic Match | Speed | Accuracy |
|----------|--------------|----------------|-------|----------|
| Pure BM25 | ✅ Excellent | ❌ Poor | ⚡ Fast | ⚠️ Limited |
| Pure Vector | ❌ Poor | ✅ Excellent | 🐢 Slow | ✅ High |
| **Hybrid (This)** | ✅ Excellent | ✅ Excellent | ⚡ Fast | ✅ Very High |

## 🚀 Quick Start

### Prerequisites

```bash
# Install Ollama (for local embeddings)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull embedding model
ollama pull mxbai-embed-large
```

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hybrid-agent-memory.git
cd hybrid-agent-memory

# Install dependencies
pip install -r requirements.txt

# Build initial index
python3 scripts/build_index.py --source-dir ./sample-docs
```

### Basic Usage

```python
from scripts.hybrid_search import HybridSearch

# Initialize searcher
searcher = HybridSearch(vector_weight=0.7, bm25_weight=0.3)

# Load your documents
documents = [
    {"id": "doc1", "content": "Your document content here..."},
    {"id": "doc2", "content": "Another document..."}
]
searcher.index_documents(documents)

# Search
results = searcher.search("your query here", top_k=5)

for result in results:
    print(f"Score: {result['combined_score']:.3f}")
    print(f"Content: {result['document']['content'][:200]}...")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Query Parser   │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   Cache      │ │   BM25   │ │    Vector    │
│   Layer      │ │  (30%)   │ │    (70%)     │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       │              └──────┬───────┘
       │                     │
       │              ┌──────▼──────┐
       │              │  Fusion     │
       │              │  Engine     │
       │              └──────┬──────┘
       │                     │
       └──────────┬──────────┘
                  ▼
         ┌────────────────┐
         │  Final Results │
         └────────────────┘
```

## 💡 Key Features

### 1. Hybrid Search (BM25 + Vector)

Combines the precision of keyword matching with the flexibility of semantic search:

```python
from scripts.hybrid_search import HybridSearch

searcher = HybridSearch(
    vector_weight=0.7,  # Semantic similarity
    bm25_weight=0.3     # Keyword matching
)
```

### 2. Intelligent Caching

```bash
# Check cache statistics
python3 scripts/search_cache.py --stats
```

### 3. Incremental Index Updates

```bash
# Update only changed files
python3 scripts/incremental_update.py
```

### 4. Search History Tracking

```bash
# View search history and feedback
python3 scripts/search_history.py --stats
```

## 📊 Performance Benchmarks

| Metric | BM25 Only | Vector Only | Hybrid | Hybrid + Cache |
|--------|-----------|-------------|--------|----------------|
| Precision@3 | 30% | 30% | **60%** | **60%** |
| Recall@5 | 100% | 80% | **100%** | **100%** |
| Avg Latency | <1ms | 1200ms | 350ms | **0ms** |
| Cache Hit Rate | N/A | N/A | N/A | **57%** |

## 🔧 Configuration

### Environment Variables

```bash
export OLLAMA_HOST=http://localhost:11434
export EMBEDDING_MODEL=mxbai-embed-large
export BM25_WEIGHT=0.3
export VECTOR_WEIGHT=0.7
export CACHE_TTL_HOURS=24
```

## 📁 Project Structure

```
hybrid-agent-memory/
├── scripts/
│   ├── hybrid_search.py          # Core hybrid search
│   ├── build_index.py            # Index construction
│   ├── incremental_update.py     # Incremental updates
│   ├── search_cache.py           # Caching layer
│   ├── search_history.py         # History tracking
│   └── compaction_guard.py       # File backup
├── docs/
│   ├── ARCHITECTURE.md           # Architecture deep dive
│   └── BENCHMARKS.md             # Performance benchmarks
├── tests/
├── requirements.txt
├── README.md
└── LICENSE
```

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [rank-bm25](https://github.com/dorianbrown/rank_bm25) for BM25 implementation
- [Ollama](https://ollama.com) for local embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for vector search

---

**Star this repo if it helps you build better AI agents!** ⭐
