# RAG Server

A simple, configurable RAG (Retrieval-Augmented Generation) system that provides intelligent access to your project documentation and code via MCP (Model Context Protocol).

> 🚀 **New to this?** Check out [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide!

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Qdrant account (free tier available at [qdrant.io](https://qdrant.io))

### Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   cd rag-server
   pip install -r requirements.txt
   ```

3. **Run setup verification:**
   ```bash
   python setup.py
   ```

4. **Configure Qdrant database:**
   
   Edit `qdrant.config.json` with your Qdrant credentials:
   ```json
   {
     "url": "https://your-cluster.qdrant.io:6333",
     "api_key": "your-api-key-here",
     "collection": "mcp-rag"
   }
   ```
   
   > 💡 **Don't have Qdrant?** Sign up for free at [qdrant.io](https://cloud.qdrant.io) and create a cluster.

5. **Create project configuration:**
   
   Create `mcp-config.json` in your **project root** (parent directory of `rag-server`):
   ```json
   {
     "cloud_qdrant": {
       "url": "env:QDRANT_CLOUD_URL",
       "api_key": "env:QDRANT_API_KEY",
       "collection": "my-project",
       "timeout": 30,
       "retry_attempts": 3
     },
     "local_qdrant": {
       "path": "./rag-server/qdrant_data",
       "collection": "my-project-local",
       "recreate_if_exists": false
     },
     "cloud_docs": [
       "docs/**/*.md",
       "README.md"
     ],
     "local_docs": [],
     "decision_log_path": "docs/decisions/",
     "code_paths": [
       "src/**/*.{py,ts,js}",
       "lib/**/*.{py,ts,js}"
     ],
     "embedding_models": {
       "doc": "sentence-transformers/all-MiniLM-L6-v2",
       "code": "microsoft/codebert-base",
       "reranking": "cross-encoder/ms-marco-MiniLM-L-6-v2"
     },
     "hybrid_retrieval": {
       "search_top_k": 20,
       "rerank_top_k": 10,
       "max_results": 25,
       "hybrid_weights": {
         "bm25": 0.3,
         "vector": 0.7
       }
     },
     "chunking": {
       "doc_chunk_size": 1000,
       "doc_chunk_overlap": 100,
       "code_chunk_strategy": "function_level",
       "code_chunk_overlap": 50
     }
   }
   ```

6. **Index your documentation and code:**
   ```bash
   python indexing/index_all.py --prune
   ```

7. **Start the server:**
   ```bash
   python main.py
   ```

That's it! Your MCP RAG server is now running. 🎉

## 📖 What This Does

This server provides three main tools:

- **`search`** - Semantic search across your documentation and code
- **`ask`** - Ask questions and get intelligent answers using RAG
- **`explain`** - Get comprehensive explanations with context

## 📁 Project Structure

```
rag-server/
├── mcp.py                  # Main CLI (user-friendly commands)
├── server.py               # MCP server entry point
├── config.py               # Configuration management
├── setup.py                # Setup verification script
├── qdrant.config.json      # Qdrant database config (create this)
├── requirements.txt        # Python dependencies
│
├── lib/                    # Library code (internal)
│   ├── core/               # Core RAG components
│   │   ├── vector_store.py
│   │   ├── embedding_manager.py
│   │   ├── query_analyzer.py
│   │   ├── reranker.py
│   │   └── answer_synthesizer.py
│   ├── indexing/           # Indexing logic
│   │   ├── index_all.py
│   │   ├── indexer.py
│   │   └── code_indexer.py
│   ├── tools/              # MCP tools
│   │   ├── search.py
│   │   ├── ask.py
│   │   └── explain.py
│   └── utils/              # Utilities
│       └── citation.py
│
├── indexing/               # Backward compatibility wrappers
├── scripts/                # Utility scripts
│   ├── verify_setup.py
│   └── check_stats.py
│
└── config/                 # Config templates
    ├── qdrant.config.example.json
    └── mcp-config.example.json
```

## 🔧 Configuration

### Qdrant Database

**Simple method (recommended):**
- Edit `qdrant.config.json` directly with your URL and API key

**Environment method:**
- Create `.env.qdrant` file (see `.env.example`)

### Project Configuration

Edit `mcp-config.json` in your project root to configure:
- **`cloud_docs`** - Documentation paths (supports glob patterns like `docs/**/*.md`)
- **`code_paths`** - Code paths to index (supports glob patterns)
- **`embedding_models`** - AI models for embeddings
- **`chunking`** - How documents are split into chunks

## 📝 Common Commands

**New User-Friendly Commands (Recommended):**

```bash
# Index everything
mcp index

# Index with cleanup
mcp index --cleanup

# Index only documentation
mcp index --docs

# Index only code
mcp index --code

# Show statistics
mcp stats

# Recover deleted chunks
mcp recover --all

# Preview deletions
mcp delete --preview

# Start server
mcp start

# Verify setup
mcp setup
```

**Legacy Commands (Still Supported):**

```bash
# Old commands still work for backward compatibility
python indexing/index_all.py --prune
python scripts/check_stats.py
python setup.py
python server.py  # (was main.py)
```

## 🔒 Security

- **Never commit** `qdrant.config.json` or `.env.qdrant` to version control
- These files are already in `.gitignore`
- Keep your API keys secure

## 🆘 Troubleshooting

**"Missing Qdrant configuration" error:**
- Make sure `qdrant.config.json` exists in `rag-server/` directory
- Or create `.env.qdrant` with your credentials

**"Missing mcp-config.json" error:**
- Create `mcp-config.json` in your project root (parent of `rag-server/`)

**Import errors:**
- Run `pip install -r requirements.txt` to install dependencies
- Make sure you're using Python 3.8+

**Indexing fails:**
- Check that your `cloud_docs` and `code_paths` in `mcp-config.json` are correct
- Verify file paths exist relative to project root

## 📚 Advanced Usage

For advanced configuration options, see:
- `docs/IMPLEMENTATION.md` - Technical implementation details
- `docs/RAG_RESEARCH_AND_RECOMMENDATIONS.md` - RAG best practices

## 🤝 Contributing

This is a reusable RAG system. Feel free to customize it for your project needs!

## 📄 License

Use this code freely in your projects.

---

**Need help?** Check the troubleshooting section or review the configuration files.
