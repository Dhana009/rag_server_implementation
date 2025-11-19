# Docker MCP Registry Submission Checklist

## ✅ Pre-Submission Checklist

### Files Created
- [x] **`Dockerfile`** at repository root
- [x] **`rag-server/tools.json`** for tool discovery
- [x] **`.dockerignore`** for optimized builds
- [x] **`DOCKER_MCP_REGISTRY.md`** - Complete submission guide

### Repository Requirements
- [ ] **License file** (MIT or Apache 2.0) - **REQUIRED**
- [x] Dockerfile in repository
- [x] Well-documented README
- [x] All sensitive files properly ignored

### Dockerfile Verification
- [x] Uses appropriate base image (Python 3.11-slim)
- [x] Installs all dependencies
- [x] Sets up MCP server correctly
- [x] Handles environment variables
- [x] Uses stdio for MCP communication

### Tools Configuration
- [x] `tools.json` file created with all 3 tools
- [x] Tool definitions match actual implementation
- [x] All parameters properly documented

## 🚀 Submission Steps

### Step 1: Add License File

**CRITICAL**: The registry requires a license file. Add one of:

**Option A: MIT License** (Recommended)
```bash
# Create LICENSE file at repository root
```

**Option B: Apache 2.0 License**
```bash
# Create LICENSE file with Apache 2.0 text
```

### Step 2: Fork Docker MCP Registry

```bash
# Fork: https://github.com/docker/mcp-registry
git clone https://github.com/YOUR_USERNAME/mcp-registry.git
cd mcp-registry
```

### Step 3: Generate Server Configuration

```bash
# Install Task if not already installed
# https://taskfile.dev/

# Run the wizard (easiest method)
task wizard

# OR use create command directly
task create -- \
  --category documentation \
  https://github.com/Dhana009/FlowHUB_Project \
  -e QDRANT_CLOUD_URL=https://your-cluster.qdrant.io:6333 \
  -e QDRANT_API_KEY=test-key \
  -e QDRANT_COLLECTION=mcp-rag \
  -e MCP_PROJECT_ROOT=/workspace
```

**Note**: The `tools.json` file will be automatically detected and used instead of running the server.

### Step 4: Copy tools.json to Registry Entry

After `task create` generates the server entry, copy `tools.json`:

```bash
# The create command creates: servers/rag-server/server.yaml
# Copy tools.json to the same directory
cp rag-server/tools.json servers/rag-server/tools.json
```

### Step 5: Test Locally

```bash
# Build and test
task build -- --tools rag-server

# Create catalog
task catalog -- rag-server

# Import to Docker Desktop
docker mcp catalog import $PWD/catalogs/rag-server/catalog.yaml

# Test in Docker Desktop MCP Toolkit
# 1. Open Docker Desktop
# 2. Go to MCP Toolkit
# 3. Configure Qdrant credentials
# 4. Enable and test the server

# Reset when done
docker mcp catalog reset
```

### Step 6: Open Pull Request

1. Commit your changes:
   ```bash
   git add servers/rag-server/
   git commit -m "Add RAG Server MCP server"
   git push
   ```

2. Open PR on GitHub:
   - Title: "Add RAG Server MCP server"
   - Description: Include what the server does, category, and any special setup requirements

3. Fill out test credentials form (if needed):
   - [Test Credentials Form](https://forms.gle/6Lw3nsvu2d6nFg8e6)

4. Wait for Docker team review

## 📋 Server Configuration Details

### Category & Tags
- **Category**: `documentation` or `code-analysis`
- **Tags**: `rag`, `semantic-search`, `documentation`, `code-search`, `vector-search`, `qdrant`

### Environment Variables

The server requires these environment variables:

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
        description: Root directory of project to index (default: /workspace)
    required:
      - qdrant_cloud_url
      - qdrant_collection
```

### Volumes

Users will mount their project directory:
- **Source**: User's project directory (configurable)
- **Destination**: `/workspace` (or as specified in `MCP_PROJECT_ROOT`)
- **Mode**: Read-only recommended for safety

## ⚠️ Important Notes

1. **License Required**: Must have MIT or Apache 2.0 license file
2. **Dockerfile Location**: At repository root (✅ created)
3. **tools.json**: Prevents build failures when listing tools (✅ created)
4. **Documentation**: Ensure README clearly explains setup requirements

## 🎯 After Approval

Once approved, your server will be available in:
- [Docker Hub MCP namespace](https://hub.docker.com/u/mcp) (within 24 hours)
- [Docker Desktop MCP Toolkit](https://www.docker.com/products/docker-desktop/)
- [MCP Catalog](https://hub.docker.com/mcp)

## 📚 Resources

- [Docker MCP Registry Contributing Guide](https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md)
- [Docker MCP Toolkit Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/)

---

**Status**: ✅ **Ready for submission after adding LICENSE file!**

