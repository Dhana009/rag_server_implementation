# Adding RAG Server to Docker MCP Registry

## ✅ Yes, It's Possible!

Your RAG server is a **Local Server (Containerized)** type, which is perfect for the Docker MCP Registry.

## 📋 Requirements Checklist

### ✅ What You Have
- ✅ MCP server implementation (3 tools: `search`, `ask`, `explain`)
- ✅ Python-based server using stdio transport
- ✅ GitHub repository: `https://github.com/Dhana009/FlowHUB_Project`
- ✅ Well-documented codebase
- ✅ MIT/Apache license (needed for registry)

### ⚠️ What You Need
- ⚠️ **Dockerfile** in the repository root (we'll create this)
- ⚠️ **License file** (MIT or Apache 2.0 recommended)
- ⚠️ **Tools can be listed** without full configuration (may need `tools.json`)

## ✅ Files Created

The following files have been created for Docker MCP Registry submission:

1. **`Dockerfile`** (repository root) - Main Dockerfile for building the image
2. **`rag-server/Dockerfile`** - Alternative Dockerfile if building from rag-server directory
3. **`rag-server/tools.json`** - Tool definitions for build-time tool discovery
4. **`.dockerignore`** - Optimizes Docker build by excluding unnecessary files

## 🚀 Steps to Add to Registry

### 1️⃣ Prerequisites

Install required tools:
```bash
# Install Go v1.24+
# Install Docker Desktop
# Install Task: https://taskfile.dev/
```

### 2️⃣ Verify Dockerfile

✅ **Dockerfile created at repository root** - Ready for Docker MCP Registry
- Uses Python 3.11-slim base image
- Installs all dependencies from `requirements.txt`
- Sets up MCP server to run via stdio
- Configures environment variables for Qdrant credentials

### 3️⃣ Fork Docker MCP Registry

```bash
# Fork: https://github.com/docker/mcp-registry
git clone https://github.com/YOUR_USERNAME/mcp-registry.git
cd mcp-registry
```

### 4️⃣ Generate Server Configuration

Use the automated wizard:

```bash
task wizard
```

Or use the create command with your GitHub repo:

```bash
task create -- \
  --category documentation \
  https://github.com/Dhana009/FlowHUB_Project \
  -e QDRANT_CLOUD_URL=https://your-cluster.qdrant.io:6333 \
  -e QDRANT_API_KEY=your-api-key \
  -e QDRANT_COLLECTION=mcp-rag \
  -e MCP_PROJECT_ROOT=/workspace \
  -e MCP_CONFIG_FILE=/app/rag-server/mcp-config.json
```

This will:
- Build your Docker image
- Test that the server can list tools
- Create `servers/rag-server/server.yaml`

### 5️⃣ Handle Configuration Challenge

✅ **tools.json created** - Located at `rag-server/tools.json`

**Important**: Your server requires Qdrant credentials to work. The registry build process needs to list tools without full configuration.

**Solution**: The `tools.json` file has been created with all 3 tools defined. When this file is found next to `server.yaml`, the build process will read tools from the file instead of running the server.

The file contains:
- `search` tool with all parameters
- `ask` tool with question and context parameters  
- `explain` tool with topic parameter

**Note**: The `tools.json` file will be copied to the registry entry directory when you run `task create`. For reference, here's what it contains:

```json
[
  {
    "name": "search",
    "description": "Semantic search with filtering across documentation and code",
    "arguments": [
      {
        "name": "query",
        "type": "string",
        "desc": "Search query string"
      },
      {
        "name": "content_type",
        "type": "string",
        "desc": "Filter by content type: 'doc', 'code', or 'all'"
      },
      {
        "name": "language",
        "type": "string",
        "desc": "Filter by language: 'python', 'typescript', 'markdown', or 'all'"
      },
      {
        "name": "top_k",
        "type": "number",
        "desc": "Number of results to return (default: 10)"
      }
    ]
  },
  {
    "name": "ask",
    "description": "Question answering with full RAG pipeline",
    "arguments": [
      {
        "name": "question",
        "type": "string",
        "desc": "The question to answer"
      },
      {
        "name": "context",
        "type": "string",
        "desc": "Optional context to help refine the answer"
      }
    ]
  },
  {
    "name": "explain",
    "description": "Get comprehensive explanations with context and rationale",
    "arguments": [
      {
        "name": "topic",
        "type": "string",
        "desc": "Topic to explain (e.g., 'phase-1 flows', 'selector policy', 'architecture rules')"
      }
    ]
  }
]
```

This prevents the build from failing when trying to list tools without Qdrant credentials.

### 6️⃣ Test Locally

```bash
# Build and test
task build -- --tools rag-server

# Create catalog
task catalog -- rag-server

# Import to Docker Desktop
docker mcp catalog import $PWD/catalogs/rag-server/catalog.yaml

# Test in Docker Desktop MCP Toolkit
# Configure Qdrant credentials in the UI
# Enable and test the server

# Reset when done
docker mcp catalog reset
```

### 7️⃣ Open Pull Request

1. Commit your changes
2. Push to your fork
3. Open PR to `docker/mcp-registry`
4. Fill out the [test credentials form](https://forms.gle/6Lw3nsvu2d6nFg8e6) if needed
5. Wait for Docker team review

## 📝 Server Configuration Details

### Category
- **Recommended**: `documentation` or `code-analysis`
- **Tags**: `rag`, `semantic-search`, `documentation`, `code-search`, `vector-search`

### Environment Variables Needed

```yaml
config:
  description: Configure Qdrant connection and project settings
  secrets:
    - name: rag-server.qdrant_api_key
      env: QDRANT_API_KEY
      example: <YOUR_QDRANT_API_KEY>
  env:
    - name: QDRANT_CLOUD_URL
      example: https://your-cluster.qdrant.io:6333
      value: '{{rag-server.qdrant_cloud_url}}'
    - name: QDRANT_COLLECTION
      example: mcp-rag
      value: '{{rag-server.qdrant_collection}}'
    - name: MCP_PROJECT_ROOT
      example: /workspace
      value: '{{rag-server.project_root}}'
  parameters:
    type: object
    properties:
      qdrant_cloud_url:
        type: string
        description: Qdrant Cloud cluster URL
      qdrant_collection:
        type: string
        description: Collection name in Qdrant
      project_root:
        type: string
        description: Root directory of project to index
    required:
      - qdrant_cloud_url
      - qdrant_collection
```

### Volumes Needed

Users will need to mount their project directory:
- Source: User's project directory
- Destination: `/workspace` (or configurable)
- Read-only: Recommended for safety

## 🎯 Benefits of Registry Inclusion

1. **Enhanced Security**: Docker-built images include:
   - Cryptographic signatures
   - Provenance tracking
   - SBOMs (Software Bill of Materials)
   - Automatic security updates

2. **Easy Discovery**: Available in:
   - [Docker Hub MCP namespace](https://hub.docker.com/u/mcp)
   - [Docker Desktop MCP Toolkit](https://www.docker.com/products/docker-desktop/)
   - [MCP Catalog](https://hub.docker.com/mcp)

3. **Better UX**: Users can:
   - Install with one click in Docker Desktop
   - Configure via UI
   - Get automatic updates

## ⚠️ Important Considerations

1. **License**: Ensure your repository has MIT or Apache 2.0 license
2. **Dockerfile Location**: Must be at repository root
3. **Tool Discovery**: Use `tools.json` if server needs config to list tools
4. **Documentation**: Ensure README is clear about setup requirements

## 📚 References

- [Docker MCP Registry Contributing Guide](https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md)
- [Docker MCP Toolkit Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/)

---

**Next Step**: Create the Dockerfile and prepare for submission! 🚀

