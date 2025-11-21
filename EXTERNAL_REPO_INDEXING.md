# Indexing Data from External Repository/Folder

When you're in a **different repository** and want to index its data into Qdrant, you have 3 options:

---

## Option 1: Use QUADRANTDB MCP Tools Directly (Easiest)

**Best for:** Adding individual files or custom data

The QUADRANTDB tools work from **anywhere** - they just need to connect to your Qdrant database.

### Steps:
1. **In Cursor**, use the MCP tools directly:
   - `add_vector` - Add content from any file/repo
   - Works from any folder/repo

2. **Example workflow:**
   ```
   # You're in: D:\my-other-project\
   # But you can still use MCP tools to add data to Qdrant
   
   # In Cursor, call:
   add_vector(
     content="<file content here>",
     metadata={
       "file_path": "D:/my-other-project/src/file.py",
       "category": "code",
       "project": "my-other-project"
     }
   )
   ```

**Pros:**
- Works from anywhere
- No config needed
- Direct control

**Cons:**
- Manual (one file at a time)
- Need to read files yourself

---

## Option 2: Create Config in External Repo (Recommended for Bulk)

**Best for:** Bulk indexing entire external repository

### Steps:

1. **In the external repository**, create `mcp-config.json`:

```json
{
  "project_root": ".",
  "local_qdrant": {
    "path": "../rag-server/qdrant_data",
    "collection": "external-project-local",
    "recreate_if_exists": false
  },
  "cloud_docs": [
    "docs/**/*.md",
    "README.md"
  ],
  "local_docs": [],
  "decision_log_path": "docs/decisions/",
  "code_paths": [
    "src/**/*.py",
    "lib/**/*.py"
  ],
  "embedding_models": {
    "doc": "sentence-transformers/all-MiniLM-L6-v2",
    "code": "microsoft/codebert-base"
  }
}
```

2. **Set environment variable** to point to rag-server's .env:
   ```bash
   # Windows PowerShell
   $env:MCP_ENV_FILE="D:\planning\rag_server_implementation\rag-server\.env.qdrant"
   
   # Or set it permanently in your system
   ```

3. **Run indexing from external repo:**
   ```bash
   # From external repo directory
   cd D:\my-other-project
   
   # Point to rag-server's indexing script
   python D:\planning\rag_server_implementation\rag-server\rag_cli.py index
   ```

**Pros:**
- Bulk indexing entire repo
- Automatic chunking
- Uses same Qdrant database

**Cons:**
- Need to create config file
- Need to set environment variable

---

## Option 3: Use Absolute Paths in Config (Alternative)

**Best for:** Multiple external repos with one config

### Steps:

1. **In rag-server's `mcp-config.json`**, use absolute paths:

```json
{
  "project_root": "D:/my-other-project",
  "cloud_docs": [
    "D:/my-other-project/docs/**/*.md",
    "D:/my-other-project/README.md"
  ],
  "code_paths": [
    "D:/my-other-project/src/**/*.py",
    "D:/my-other-project/lib/**/*.py"
  ]
}
```

2. **Run indexing from rag-server:**
   ```bash
   cd D:\planning\rag_server_implementation\rag-server
   python rag_cli.py index
   ```

**Pros:**
- One config for multiple repos
- Run from rag-server directory

**Cons:**
- Hardcoded paths
- Less flexible

---

## Recommended Workflow

### For Initial Setup (External Repo):
```bash
# 1. Go to external repo
cd D:\my-other-project

# 2. Create mcp-config.json (see Option 2 above)

# 3. Set environment variable
$env:MCP_ENV_FILE="D:\planning\rag_server_implementation\rag-server\.env.qdrant"

# 4. Run indexing
python D:\planning\rag_server_implementation\rag-server\rag_cli.py index
```

### For Adding Individual Files (Any Repo):
- Use QUADRANTDB MCP tools in Cursor
- Works from anywhere
- No config needed

---

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `MCP_ENV_FILE` | Path to .env with Qdrant credentials | `D:\planning\rag_server_implementation\rag-server\.env.qdrant` |
| `MCP_CONFIG_FILE` | Path to mcp-config.json | `D:\my-other-project\mcp-config.json` |
| `MCP_PROJECT_ROOT` | Override project root | `D:\my-other-project` |

---

## Summary

- **QUADRANTDB MCP Tools**: Use from anywhere, manual control
- **Config in External Repo**: Best for bulk indexing external repos
- **Absolute Paths**: One config, multiple repos

All methods connect to the **same Qdrant database** - they just index different source data!

