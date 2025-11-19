# RAG Server

A production-ready RAG (Retrieval-Augmented Generation) system for MCP (Model Context Protocol). Provides intelligent semantic search and question-answering capabilities for your codebase and documentation.

## Features

- 🔍 **Hybrid Search**: Combines vector similarity and BM25 keyword search
- 📚 **Multi-Format Support**: Indexes documentation (Markdown) and code (Python, TypeScript, JavaScript)
- 🎯 **Intent-Aware**: Automatically classifies queries and optimizes retrieval
- 🔄 **Incremental Updates**: Efficient re-indexing of changed files
- ☁️ **Cloud & Local**: Supports both Qdrant Cloud and local instances
- 🛠️ **MCP Integration**: Seamless integration with Cursor IDE and other MCP clients
- ⚡ **Production-Ready**: Error handling, logging, and comprehensive testing

## Quick Start

### For AI Assistants

Run the automated setup script:

```bash
python rag-server/auto_setup.py
```

This will automatically:
- ✅ Verify Python version (3.8+)
- ✅ Install all dependencies
- ✅ Create configuration files with auto-detected paths
- ✅ Configure Cursor IDE integration
- ✅ Verify the setup

### For Users

1. **Install dependencies:**
   ```bash
   cd rag-server
   pip install -r requirements.txt
   ```

2. **Configure Qdrant:**
   Edit `rag-server/qdrant.config.json` with your credentials:
   ```json
   {
     "url": "https://your-cluster.qdrant.io:6333",
     "api_key": "your-api-key-here",
     "collection": "mcp-rag"
   }
   ```
   
3. **Configure project:**
   Edit `rag-server/mcp-config.json` to specify what to index:
   ```json
   {
     "project_root": "..",
     "cloud_docs": ["docs/**/*.md", "README.md"],
     "code_paths": ["src/**/*.py", "lib/**/*.py"]
   }
   ```

4. **Index content:**
   ```bash
   python rag_cli.py index
   ```

5. **Verify:**
   ```bash
   python rag_cli.py stats
   ```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Qdrant Cloud account (or local Qdrant instance)

### Step-by-Step Setup

#### 1. Clone or Navigate to Project

```bash
cd your-project
# If rag-server is already in your project, skip to step 2
```

#### 2. Install Dependencies

```bash
cd rag-server
pip install -r requirements.txt
```

**Required packages:**
- `qdrant-client` - Vector database client
- `sentence-transformers` - Document embeddings
- `transformers` - Code embeddings and reranking
- `mcp` - Model Context Protocol
- `pydantic` - Configuration validation
- `python-dotenv` - Environment variable management
- `tree-sitter` - Code parsing

#### 3. Get Qdrant Credentials

**Option A: Qdrant Cloud (Recommended)**
1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a free cluster
3. Copy your cluster URL and API key

**Option B: Local Qdrant**
1. Install Qdrant locally: `docker run -p 6333:6333 qdrant/qdrant`
2. Use `http://localhost:6333` as URL
3. No API key needed for local instances

#### 4. Configure Qdrant Connection

Create or edit `rag-server/qdrant.config.json`:

```json
{
  "url": "https://your-cluster.qdrant.io:6333",
  "api_key": "your-api-key-here",
  "collection": "mcp-rag"
}
```

#### 5. Configure Project Paths

Create or edit `rag-server/mcp-config.json`:

```json
{
  "project_root": "..",
     "cloud_docs": [
       "docs/**/*.md",
    "README.md",
    "CHANGELOG.md"
     ],
     "code_paths": [
    "src/**/*.py",
    "lib/**/*.py",
    "app/**/*.{py,ts,js}"
  ],
  "local_qdrant": {
    "path": "./qdrant_data",
    "collection": "mcp-rag-local"
  }
}
```

**Configuration fields:**
- `project_root`: Root directory of your project (relative to `rag-server/`)
- `cloud_docs`: Glob patterns for documentation files
- `code_paths`: Glob patterns for code files
- `local_qdrant`: Local Qdrant configuration (optional)

#### 6. Verify Setup

```bash
python setup.py
```

This checks:
- Python version compatibility
- Installed dependencies
- Configuration file validity
- Qdrant connection (if credentials provided)

#### 7. Index Your Content

```bash
# Index everything (docs + code)
python rag_cli.py index

# Or index separately:
python rag_cli.py index --docs    # Documentation only
python rag_cli.py index --code    # Code only
```

**First-time indexing:**
- Downloads embedding models (~500MB) on first run
- May take several minutes depending on project size
- Progress is shown in terminal

#### 8. Check Status

```bash
python rag_cli.py stats
```

You should see:
- Number of documents indexed
- Number of code chunks indexed
- Collection size and statistics

## Configuration

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `mcp-config.json` | `rag-server/` | Project configuration (paths, models, retrieval settings) |
| `qdrant.config.json` | `rag-server/` | Database connection (URL, API key, collection) |

Both files are located in `rag-server/` for easy management.

### Environment Variables

You can override configuration paths using environment variables:

```bash
export MCP_PROJECT_ROOT="/path/to/project"
export MCP_CONFIG_FILE="/path/to/mcp-config.json"
export MCP_ENV_FILE="/path/to/.env.qdrant"
export MCP_SERVER_NAME="my-rag-server"
```

### Advanced Configuration

The `mcp-config.json` supports advanced settings:

```json
{
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

See `config/mcp-config.example.json` for full configuration options.

## Usage

### Command-Line Interface

The `rag_cli.py` script provides a unified CLI for all operations:

   ```bash
# Indexing
python rag_cli.py index                      # Index everything (incremental - only updates what changed)
python rag_cli.py index --docs               # Index docs only
python rag_cli.py index --code               # Index code only
python rag_cli.py index --cleanup --dry-run  # Preview cleanup (safe, shows what would be deleted)
python rag_cli.py index --cleanup            # Index + soft-delete orphaned chunks (recoverable)
python rag_cli.py index --cloud              # Use cloud collection only
python rag_cli.py index --local              # Use local collection only

**Note**: Indexing is incremental by default. It automatically:
- ✅ Detects new files and indexes them
- ✅ Updates only modified chunks (skips unchanged content)
- ✅ Prevents duplicates automatically
- ✅ Safe to run multiple times

See `docs/INCREMENTAL_INDEXING.md` for detailed explanation of how incremental updates and duplicate prevention work.

# Statistics
python rag_cli.py stats              # Show all collection stats
python rag_cli.py stats --cloud      # Cloud collection only
python rag_cli.py stats --local      # Local collection only

# Data Management

## Understanding Deletion Commands

The system uses a **two-stage deletion** process for safety:

### Stage 1: Soft-Delete (Mark as Deleted)
```bash
python rag_cli.py index --cleanup --dry-run    # Preview what would be soft-deleted (safe)
python rag_cli.py index --cleanup              # Actually soft-delete chunks from removed files (recoverable)
```
- **What it does**: Marks chunks from files no longer in config as `is_deleted: true`
- **Recoverable**: Yes, can be recovered with `recover` command
- **Safe**: Chunks are hidden from search but not removed
- **When to use**: After removing files from `mcp-config.json`
- **Preview first**: Use `--dry-run` to see what would be deleted before actually doing it

### Stage 2: Permanent Delete (Actually Remove)
```bash
python rag_cli.py delete --preview   # Preview what would be permanently deleted (safe)
python rag_cli.py delete --confirm   # Permanently delete soft-deleted chunks (destructive)
```
- **What it does**: Physically removes soft-deleted chunks from database
- **Recoverable**: No, cannot be recovered after this
- **When to use**: After verifying with `--preview`, when you're sure you don't need the data

### Complete Cleanup (Nuclear Option)
```bash
python rag_cli.py clean              # Delete ALL data from database (WARNING: very destructive)
```
- **What it does**: Deletes **everything** (all chunks, not just soft-deleted)
- **Recoverable**: No
- **When to use**: Starting fresh, complete reset

### Recovery
```bash
python rag_cli.py recover --all      # Recover all soft-deleted chunks
python rag_cli.py recover --file <path>  # Recover chunks for specific file
```
- **What it does**: Restores soft-deleted chunks (marks `is_deleted: false`)
- **When to use**: If you accidentally deleted files or want to restore them

## Quick Reference Table

| Command | What It Does | Recoverable? | Safety |
|---------|--------------|--------------|--------|
| `index --cleanup --dry-run` | Preview what would be soft-deleted | N/A | Safe (read-only) |
| `index --cleanup` | Soft-deletes chunks from removed files | ✅ Yes | Safe |
| `delete --preview` | Preview what would be permanently deleted | N/A | Safe (read-only) |
| `delete --confirm` | Permanently deletes soft-deleted chunks | ❌ No | Destructive |
| `recover --all` | Restores all soft-deleted chunks | N/A | Safe |
| `clean` | Deletes **ALL** data (everything) | ❌ No | Very Destructive |

## Recommended Workflow

1. **Remove files from config** → Edit `mcp-config.json`
2. **Preview cleanup** → `python rag_cli.py index --cleanup --dry-run` (see what would be deleted)
3. **Soft-delete** → `python rag_cli.py index --cleanup` (mark as deleted, recoverable)
4. **Verify permanent delete** → `python rag_cli.py delete --preview` (check what would be permanently removed)
5. **Permanent delete** (optional) → `python rag_cli.py delete --confirm` (only if you're sure)

# Server
python rag_cli.py start              # Start MCP server (standalone/testing mode)
python rag_cli.py setup              # Verify setup and configuration
```

### MCP Server Integration

#### Cursor IDE

The automated setup script configures Cursor automatically. To configure manually:

1. Edit `~/.cursor/mcp.json` (Windows: `C:\Users\<YourUsername>\.cursor\mcp.json`):

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "C:\\Python313\\python.exe",
      "args": ["D:/path/to/rag-server/server.py"]
    }
  }
}
```

2. Restart Cursor IDE

3. The RAG server will appear in Cursor's MCP panel

#### Available MCP Tools

Once connected, the following tools are available:

- **`search`**: Semantic search with filtering
  - Parameters: `query`, `type` (docs/code/all), `limit`
  
- **`ask`**: Question answering with full RAG pipeline
  - Parameters: `question`, `context` (optional)
  
- **`explain`**: Comprehensive explanations with context
  - Parameters: `topic`, `depth` (optional)

### How the Server Works

**Important:** The RAG server is an MCP (Model Context Protocol) server that communicates via **stdio** (standard input/output) using JSON-RPC. This means:

1. **Normal Usage**: The server is automatically started by Cursor IDE (or other MCP clients) when you use it
2. **You don't manually start it**: Once configured in Cursor, it runs automatically in the background
3. **Standalone mode**: Only for testing/debugging - the server will start but wait for JSON-RPC messages

#### How It Works in Cursor IDE

1. **Configuration**: Add server to `~/.cursor/mcp.json` (done automatically by `auto_setup.py`)
2. **Auto-start**: Cursor IDE automatically starts the server when you open it
3. **Usage**: Use the tools through Cursor's chat interface - the server runs in the background
4. **No manual start needed**: The server is managed by Cursor IDE

#### Testing the Server

**Option 1: Verify Components (Recommended)**
```bash
# Check all components load correctly
python scripts/verify_setup.py

# Run full test suite
python scripts/test_rag_system.py
```

**Test with Custom Instructions**:
The `custominstructions/` folder contains test files for validating functionality. 

**For AI Assistants**: See `custominstructions/AI_TESTING_INSTRUCTIONS.md` for step-by-step testing procedures.

**For Users**: See `custominstructions/TEST_GUIDE.md` for detailed testing guide.

**Option 2: Test Server Startup (Standalone Mode)**
```bash
# This starts the server and waits for JSON-RPC input
# It will appear to "hang" - this is normal! It's waiting for commands
python rag_cli.py start

# Or directly:
python server.py
```

**Note:** In standalone mode, the server will:
- ✅ Start successfully and show "waiting for connections"
- ✅ Log to `rag-server.log` and stderr
- ⚠️ Appear to "hang" - this is normal! It's waiting for JSON-RPC messages
- ⚠️ You can't interact with it directly from the terminal
- ⚠️ Press `Ctrl+C` to stop it

**To actually use the server**, you need to:
1. Configure it in Cursor IDE (see "MCP Server Integration" above)
2. Restart Cursor IDE
3. Use it through Cursor's chat interface

#### Verifying Server is Running in Cursor

1. Open Cursor IDE
2. Check the MCP panel (usually in the sidebar or status bar)
3. Look for your RAG server in the list
4. If it shows as "connected" or "active", it's working!
5. Try asking a question in Cursor's chat about your codebase

## Project Structure

```
rag-server/
├── rag_cli.py                  # Unified CLI
├── server.py                   # MCP server entry point
├── config.py                   # Configuration management
├── setup.py                    # Setup verification
├── auto_setup.py               # Automated setup script
├── qdrant.config.json          # Database config (user-created)
├── mcp-config.json             # Project config (user-created)
├── requirements.txt            # Python dependencies
│
├── lib/                        # Core library
│   ├── core/                   # Core RAG components
│   │   ├── embedding_manager.py
│   │   ├── query_analyzer.py
│   │   ├── vector_store.py
│   │   ├── reranker.py
│   │   └── answer_synthesizer.py
│   ├── indexing/               # Indexing logic
│   │   ├── indexer.py
│   │   ├── code_parser.py
│   │   ├── code_chunker.py
│   │   └── code_indexer.py
│   ├── tools/                  # MCP tools
│   │   ├── search.py
│   │   ├── ask.py
│   │   └── explain.py
│   └── utils/                  # Utilities
│       └── citation.py
│
├── scripts/                    # Utility scripts
│   ├── check_stats.py
│   ├── clean_database.py
│   ├── recover_deleted.py
│   ├── permanent_delete.py
│   ├── verify_setup.py
│   └── test_rag_system.py
│
├── config/                     # Configuration examples
│   ├── mcp-config.example.json
│   └── qdrant.config.example.json
│
└── docs/                       # Documentation
    ├── IMPLEMENTATION.md
    └── RAG_RESEARCH_AND_RECOMMENDATIONS.md
```

## Troubleshooting

### Common Issues

**"Missing Qdrant configuration" error:**
- Ensure `qdrant.config.json` exists in `rag-server/`
- Verify URL and API key are correct
- Test connection: `python -c "from config import load_config; c = load_config()"`

**"No documents found" during indexing:**
- Check `mcp-config.json` paths are correct
- Verify files exist at specified paths
- Use absolute paths if relative paths don't work
- Check file permissions

**Server not appearing in Cursor:**
- Verify `mcp.json` was updated correctly
- Check Python path in `mcp.json` matches your executable
- Restart Cursor completely (not just reload)
- Check `rag-server.log` for errors
- Verify server can start: `python rag_cli.py start` (should show "waiting for connections")

**Server appears to hang when running standalone:**
- This is **normal behavior**! The server uses stdio (standard input/output) for JSON-RPC communication
- It's waiting for JSON-RPC messages from an MCP client (like Cursor IDE)
- You can't interact with it directly from the terminal
- To actually use it, configure it in Cursor IDE and use it through Cursor's interface

**Slow indexing:**
- Normal for first-time indexing (models download ~500MB)
- Subsequent indexing is much faster
- Consider using `--docs` or `--code` flags to index separately

**Import errors:**
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.8+)
- Try: `python setup.py` to verify installation

**Qdrant connection timeout:**
- Check network connectivity
- Verify Qdrant cluster is running
- Check firewall settings
- For local Qdrant: ensure Docker container is running

### Getting Help

1. Check `rag-server.log` for detailed error messages
2. Run `python rag_cli.py setup` to verify configuration
3. Run `python scripts/verify_setup.py` to check components
4. Review configuration files against examples in `config/`

## Advanced Usage

### Incremental Indexing

The system automatically tracks file changes and only re-indexes modified files:

```bash
python rag_cli.py index  # Only changed files are re-indexed
```

### Cloud vs Local Collections

Use different collections for different purposes:

```bash
# Index to cloud (production)
python rag_cli.py index --cloud

# Index to local (development/testing)
python rag_cli.py index --local
```

### Data Recovery

If chunks are accidentally soft-deleted:

```bash
# Preview what can be recovered
python rag_cli.py recover --all

# Recover all deleted chunks
python rag_cli.py recover --all --confirm
```

### Cleanup Orphaned Chunks

Remove chunks for files that no longer exist:

```bash
python rag_cli.py index --cleanup
```

## AI Setup Instructions (For AI Assistants)

If you're an AI assistant setting up this project, use the automated setup script:

```bash
python rag-server/auto_setup.py
```

The script handles:
- Python version verification
- Dependency installation
- Configuration file creation with auto-detection
- Cursor IDE integration
- Setup verification

**Manual setup steps** (if needed):

1. **Verify Python:**
   ```python
   import sys
   assert sys.version_info >= (3, 8), "Python 3.8+ required"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create configs:**
   - Copy `config/qdrant.config.example.json` to `qdrant.config.json`
   - Copy `config/mcp-config.example.json` to `mcp-config.json`
   - Auto-detect project paths and update configs

4. **Configure Cursor:**
   - Detect Cursor config location (platform-specific)
   - Add server entry to `mcp.json`
   - Use detected Python executable and server path

5. **Verify:**
   ```bash
   python setup.py
   ```

See `auto_setup.py` for the complete implementation.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Changelog

See `CHANGELOG.md` for version history and updates.
