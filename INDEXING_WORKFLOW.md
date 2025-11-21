# QUADRANTDB Tools vs Bulk Indexing - Workflow Guide

## Two Different Use Cases

### 1. **Bulk Indexing (Initial Setup & Updates)**
**Use CLI scripts** to index all your documents and code at once.

```bash
# Index everything (docs + code)
python rag_cli.py index

# Index only documentation
python rag_cli.py index --docs

# Index only code
python rag_cli.py index --code

# Index to cloud collection only
python rag_cli.py index --cloud

# Index to local collection only
python rag_cli.py index --local
```

**What it does:**
- Reads `mcp-config.json` for paths
- Finds all `.md` files (docs) and code files (`.py`, `.ts`, etc.)
- Chunks them automatically
- Generates embeddings
- Stores in Qdrant using `HybridVectorStore.index_doc()`
- Handles incremental updates (only updates changed chunks)

**When to use:**
- Initial setup (first time indexing)
- After adding new files
- After updating existing files
- Regular maintenance

---

### 2. **Individual Vector Operations (MCP Tools)**
**Use QUADRANTDB MCP tools** for programmatic/manual vector operations.

**Available Tools:**
1. `add_vector` - Add single vector with content/metadata
2. `get_vector` - Retrieve vector by ID
3. `update_vector` - Update vector content/metadata
4. `delete_vector` - Delete vector (soft or hard)
5. `search_similar` - Semantic similarity search
6. `search_by_metadata` - Filter by metadata

**When to use:**
- Adding custom test data
- Storing logs or temporary data
- Manual vector operations
- Programmatic access from AI agents
- Testing and debugging

---

## Complete Workflow Example

### Step 1: Initial Bulk Indexing
```bash
# First time - index everything
cd rag-server
python rag_cli.py index
```

This will:
- Index all docs from `config.cloud_docs` patterns
- Index all code from `config.code_paths` patterns
- Store in Qdrant collections

### Step 2: Use MCP Tools for Individual Operations
In Cursor, you can now use:
- `add_vector` to add custom data
- `search_similar` to find relevant content
- `get_vector` to retrieve specific vectors
- etc.

### Step 3: Update Index When Files Change
```bash
# Re-index after making changes
python rag_cli.py index

# Or just update docs
python rag_cli.py index --docs

# Or just update code
python rag_cli.py index --code
```

---

## Key Difference

| Feature | Bulk Indexing (CLI) | QUADRANTDB Tools (MCP) |
|---------|---------------------|------------------------|
| **Purpose** | Index entire codebase/docs | Individual vector operations |
| **Input** | File paths from config | Raw content + metadata |
| **Chunking** | Automatic (by file) | Manual (you provide content) |
| **Embedding** | Automatic | Automatic (if content provided) |
| **Use Case** | Initial setup, updates | Custom data, testing, programmatic access |
| **Interface** | Command line | MCP protocol (Cursor) |

---

## Summary

- **Bulk Indexing**: `python rag_cli.py index` - for indexing all your files
- **QUADRANTDB Tools**: MCP tools in Cursor - for individual vector operations

Both work together! Use bulk indexing for your codebase, use QUADRANTDB tools for custom operations.

