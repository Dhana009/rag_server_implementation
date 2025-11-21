# Vector CRUD Tools Implementation Plan

## Overview
Add MCP tools to expose vector database CRUD operations (add, update, delete, read, stats) for the Qdrant cloud collection. Support both point-level and document-level operations with flexible input formats.

## Implementation Architecture

### Code Structure
- **Single File**: `rag-server/lib/tools/vector_crud.py` - All CRUD tools in one file
- **Helper Methods**: Add to `HybridVectorStore` class in `vector_store.py`
- **Error Handling**: Custom exception classes in `vector_store.py`
- **Validation**: Tool-level validation before calling vector_store
- **Config Access**: Dependency injection - pass config/store to tool functions

### Response Format (Consistent JSON)
```json
{
  "success": true/false,
  "data": {...},
  "metadata": {
    "count": int,
    "timing_ms": float,
    "operation": str
  },
  "errors": [...],
  "version": "..." (optional)
}
```

### Error Structure (Structured)
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Error description",
  "details": {...},
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}
```

## Implementation Steps

### Step 1: Create Custom Exception Classes
**File**: `rag-server/lib/core/vector_store.py`

Add at top of file:
```python
class VectorStoreError(Exception):
    """Base exception for vector store operations"""
    def __init__(self, code: str, message: str, details: dict = None, suggestions: list = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.suggestions = suggestions or []
        super().__init__(self.message)

class ValidationError(VectorStoreError):
    """Input validation failures"""
    pass

class PointNotFoundError(VectorStoreError):
    """Point ID not found"""
    pass

class DimensionMismatchError(VectorStoreError):
    """Vector dimension issues"""
    pass

class BatchLimitExceededError(VectorStoreError):
    """Batch size too large"""
    pass
```

### Step 2: Extend HybridVectorStore with Helper Methods
**File**: `rag-server/lib/core/vector_store.py`

Add methods to `HybridVectorStore` class:

1. **`generate_point_id(content: str, file_path: str, line_start: int) -> int`**
   - Hash-based deterministic ID generation
   - Same input = same ID (prevents duplicates, ensures idempotency)
   - Use: `abs(hash(f"{file_path}:{line_start}")) % (2**63 - 1)`

2. **`create_point_struct(point_id: int, vector: List[float], payload: Dict) -> PointStruct`**
   - Helper for creating PointStruct objects
   - Ensures consistent formatting

3. **`encode_content(content: str) -> List[float]`**
   - Generate embeddings from content
   - Use existing embedder
   - Handle UTF-8 normalization, whitespace

4. **`validate_vector(vector: List[float], expected_dim: Optional[int] = None) -> bool`**
   - Comprehensive validation: dimension, type, range checks
   - If expected_dim not provided, use self.vector_size from config
   - Raise DimensionMismatchError on failure

5. **`parse_filter(filter_dict: Dict) -> Filter`**
   - Convert JSON dict to Qdrant Filter object
   - Support must/should/must_not structure
   - Handle FieldCondition, MatchValue, etc.

6. **`ensure_collection_exists(collection: str = "cloud")`**
   - Auto-create collection if missing
   - Use existing `_ensure_collection` method

7. **`chunk_batch(items: List, batch_size: int) -> List[List]`**
   - Chunk items into smaller batches
   - Default batch_size: 100

### Step 3: Create Vector CRUD Tool File
**File**: `rag-server/lib/tools/vector_crud.py`

Follow pattern from `search.py`:
- Import dependencies (HybridVectorStore, load_config, etc.)
- Use dependency injection pattern
- Implement all 10 tool functions
- Define MCP Tool schemas

#### Point-Level Operations

**1. `add_points_tool(points: List[Dict], batch_size: int = 100, include_vectors: bool = True) -> str`**
- Accept points with `content` (auto-embed) OR `vector` (raw)
- Validate each point (required fields, vector dimension if provided)
- Auto-generate IDs using `store.generate_point_id()`
- Process in batches using `store.chunk_batch()`
- For each batch:
  - Generate embeddings for content-based points
  - Create PointStruct objects
  - Upsert to cloud collection
- Return: JSON with generated IDs, counts, timing, errors
- Handle partial failures with detailed report

**2. `update_points_tool(points: List[Dict], upsert: bool = True, batch_size: int = 100) -> str`**
- Similar to add_points but for updates
- Upsert mode by default (create if not exists)
- Validate point IDs exist (unless upsert=True)
- Batch processing with detailed success/failure report

**3. `delete_points_tool(point_ids: Optional[List[int]] = None, filter: Optional[Dict] = None, soft_delete: bool = False, dry_run: bool = False) -> str`**
- Support three modes:
  - ID-based: `point_ids` provided
  - Filter-based: `filter` dict provided (convert to Qdrant Filter)
  - Query-based: Use semantic search to find points (if needed)
- Soft-delete: Set `is_deleted: True` in payload
- Hard-delete: Remove from Qdrant
- Dry-run: Validate and simulate, return preview without executing
- Return: Count of affected points, preview in dry-run mode

**4. `get_points_tool(point_ids: List[int], include_vectors: bool = False) -> str`**
- Retrieve points by IDs
- Optional vector inclusion (default: False to reduce response size)
- Return: Formatted JSON with point data

**5. `query_points_tool(query: Optional[str] = None, filter: Optional[Dict] = None, limit: int = 10, offset: int = 0, include_vectors: bool = False) -> str`**
- Full query capabilities:
  - Semantic search if `query` provided
  - Filter-based if `filter` provided
  - Vector similarity if vector provided
  - Combine multiple methods
- Offset-based pagination (limit + offset)
- Default limit: 10, max: 1000
- Format results similar to search tool
- Return: Paginated, formatted results

#### Document-Level Operations

**6. `add_document_tool(doc_path: str, chunks: List[Dict]) -> str`**
- Pre-chunked input (matches index_doc pattern)
- Validate required fields: `file_path`, `line_start`, `line_end` in each chunk
- Moderate validation: validate structure and required, warn on missing optional
- Wrap existing `store.index_doc(doc_path, "cloud", chunks)`
- Return: JSON with operation result, counts, timing

**7. `update_document_tool(doc_path: str, chunks: List[Dict]) -> str`**
- Same as add_document (index_doc handles updates automatically)
- Wrapper around `store.index_doc()`

**8. `delete_document_tool(doc_path: str, soft_delete: bool = False, dry_run: bool = False) -> str`**
- Delete all points for a document
- Use filter: `file_path == doc_path`
- Support soft/hard delete
- Dry-run mode with preview
- Return: Count of deleted points

**9. `get_document_tool(doc_path: str, include_vectors: bool = False) -> str`**
- Get all points for a document
- Use filter: `file_path == doc_path`
- Return: All chunks for the document

#### Stats Operation

**10. `get_collection_stats_tool(include_version: bool = False) -> str`**
- Get detailed stats: point count, size, indexes, configuration
- Use existing `store.get_collection_stats()`
- Optional version info (read from package `__version__`)
- Return: Detailed stats JSON

### Step 4: Define MCP Tool Schemas
**File**: `rag-server/lib/tools/vector_crud.py`

For each tool function, define corresponding MCP Tool:
```python
add_points_tool_mcp = Tool(
    name="add_points",
    description="Add points to vector store. Accepts content (auto-embeds) or raw vectors. Returns generated IDs.",
    inputSchema={
        "type": "object",
        "properties": {
            "points": {
                "type": "array",
                "description": "Array of points to add",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Text content (auto-embedded)"},
                        "vector": {"type": "array", "description": "Raw vector (384 dimensions)"},
                        "payload": {"type": "object", "description": "Metadata payload"}
                    }
                }
            },
            "batch_size": {"type": "integer", "default": 100, "description": "Batch size for processing"},
            "include_vectors": {"type": "boolean", "default": True, "description": "Include vectors in response"}
        },
        "required": ["points"]
    }
)
```

Include JSON examples in tool descriptions showing real-world QA automation use cases.

### Step 5: Update Tool Manifest
**File**: `rag-server/lib/core/tool_manifest.py`

Add ToolBrief entries in `TOOL_BRIEFS` dict:
```python
"add_points": ToolBrief(
    name="add_points",
    brief="Add points to vector store. Accepts content (auto-embeds) or raw vectors. Returns generated IDs.",
    category="vector_operations",
    use_cases=["Add test data to vector store", "Index custom content for RAG"]
),
# ... repeat for all 10 tools
```

Keep briefs within 30-50 token limit.

### Step 6: Update Manifest Tool Enum
**File**: `rag-server/lib/tools/manifest.py`

Update `get_tool_schema_tool_mcp` inputSchema enum:
```python
"enum": [
    "search", "ask", "explain",
    "add_points", "update_points", "delete_points", "get_points", "query_points",
    "add_document", "update_document", "delete_document", "get_document",
    "get_collection_stats"
]
```

### Step 7: Register Tools in Server
**File**: `rag-server/server.py`

1. Import all tools:
```python
from lib.tools.vector_crud import (
    add_points_tool, update_points_tool, delete_points_tool,
    get_points_tool, query_points_tool,
    add_document_tool, update_document_tool, delete_document_tool,
    get_document_tool, get_collection_stats_tool,
    add_points_tool_mcp, update_points_tool_mcp, delete_points_tool_mcp,
    get_points_tool_mcp, query_points_tool_mcp,
    add_document_tool_mcp, update_document_tool_mcp, delete_document_tool_mcp,
    get_document_tool_mcp, get_collection_stats_tool_mcp
)
```

2. Add to `ALL_TOOLS` list:
```python
ALL_TOOLS = [
    # Existing tools...
    add_points_tool_mcp,
    update_points_tool_mcp,
    delete_points_tool_mcp,
    get_points_tool_mcp,
    query_points_tool_mcp,
    add_document_tool_mcp,
    update_document_tool_mcp,
    delete_document_tool_mcp,
    get_document_tool_mcp,
    get_collection_stats_tool_mcp
]
```

3. Register schemas:
```python
ToolManifest.register_tool_schema(
    "add_points",
    add_points_tool_mcp.description,
    add_points_tool_mcp.inputSchema,
    examples=[
        {"points": [{"content": "Test data", "payload": {"file_path": "test.md"}}], "batch_size": 50},
        {"points": [{"vector": [0.1]*384, "payload": {"custom": "data"}}]}
    ]
)
# ... repeat for all tools
```

4. Add handlers in `call_tool()`:
```python
elif name == "add_points":
    points = arguments.get("points", [])
    batch_size = arguments.get("batch_size", 100)
    include_vectors = arguments.get("include_vectors", True)
    result = add_points_tool(points, batch_size, include_vectors)
# ... repeat for all tools
```

## Key Implementation Details

### Timing
- Use `time.time()` at start/end of each operation
- Include timing in response metadata as `timing_ms`

### Logging
- Structured logging: `logger.info(f"Operation: {op}, Count: {count}, Timing: {timing}ms")`
- Log operations, counts, timing, errors

### Validation
- Tool-level validation before calling vector_store
- Moderate strictness: validate critical fields, warn on suspicious inputs
- Validate required fields, allow empty optional metadata

### Batch Processing
- Chunk into configurable batches (default: 100)
- Process sequentially (not parallel)
- Best effort: process all, report successes/failures
- Detailed report for partial failures

### Error Handling
- Use custom exceptions
- Structured error responses with code, message, details, suggestions
- Error suggestion mapping dictionary
- Empty results return structured response with count=0 (not error)

### Idempotency
- Deterministic ID generation + upsert operations
- Same input = same result (safe to retry)

### Collection Management
- Default to cloud collection (no parameter needed)
- Auto-create collection if missing
- Use existing `_ensure_collection` method

## Testing Checklist

- [ ] All 10 tools appear in manifest
- [ ] Tool schemas can be retrieved via get_tool_schema
- [ ] Examples are included in schemas
- [ ] Tools handle errors gracefully
- [ ] Batch operations work correctly
- [ ] Pagination works for query operations
- [ ] Dry-run mode works for delete operations
- [ ] Soft-delete vs hard-delete works correctly
- [ ] Response format is consistent across all tools
- [ ] Timing is included in responses
- [ ] Logging works correctly






