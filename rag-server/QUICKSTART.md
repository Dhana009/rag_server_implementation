# 🚀 Quick Start Guide

Get your RAG Server running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd rag-server
pip install -r requirements.txt
```

## Step 2: Configure Qdrant

1. Get your Qdrant credentials from [qdrant.io](https://cloud.qdrant.io)

2. Copy the example config:
   ```bash
   cp config/qdrant.config.example.json qdrant.config.json
   ```

3. Edit `qdrant.config.json`:
   ```json
   {
     "url": "https://your-cluster.qdrant.io:6333",
     "api_key": "your-actual-api-key",
     "collection": "mcp-rag"
   }
   ```

## Step 3: Configure Your Project

1. Go to your project root (parent of `rag-server/`)

2. Copy the example config:
   ```bash
   cp rag-server/config/mcp-config.example.json mcp-config.json
   ```

3. Edit `mcp-config.json` to point to your docs and code:
   ```json
   {
     "cloud_docs": [
       "docs/**/*.md",
       "README.md"
     ],
     "code_paths": [
       "src/**/*.{py,ts,js}"
     ]
   }
   ```

## Step 4: Index Your Content

```bash
cd rag-server
mcp index --cleanup
```

Or use the legacy command:
```bash
python indexing/index_all.py --prune
```

This will index all your documentation and code.

## Step 5: Start the Server

```bash
mcp start
```

Or use the legacy command:
```bash
python server.py
```

Done! Your server is now running. 🎉

## Need Help?

- Run `python setup.py` to verify your setup
- Check `README.md` for detailed documentation
- See troubleshooting section in README

