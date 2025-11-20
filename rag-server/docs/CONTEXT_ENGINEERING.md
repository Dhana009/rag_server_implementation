# Context Engineering Optimization - Implementation Guide

**Date**: 2025-01-20  
**Status**: ✅ Implemented  
**Purpose**: Prevent context rot by implementing three-tier context engineering for MCP tools

---

## Overview

This RAG server implements **three-tier context engineering** to optimize context window usage and prevent context rot when using MCP servers. Instead of loading all tool schemas upfront, tools are loaded progressively based on need.

---

## The Problem: MCP Context Rot

**Context Rot** occurs when:
- All MCP tool schemas are loaded upfront
- Context window fills with unused tool definitions
- Performance degrades as more tools are added
- AI assistants struggle with large tool lists

**Traditional Approach** (❌ Inefficient):
```
Load ALL tool schemas → Use 1-2 tools → Context wasted
```

**Context Engineering Approach** (✅ Efficient):
```
Load briefs → Select tool → Load schema → Execute
```

---

## Three-Tier Architecture

### Tier 1: Tool Manifest (Always Loaded)

**Purpose**: Lightweight tool discovery (~30-50 tokens per tool)

**Tool**: `get_manifest`

**Returns**:
- Tool name
- Brief description (~30-50 tokens)
- Category (search, qa, explanation)
- 2-3 key use cases

**Example**:
```json
{
  "manifest": {
    "search": {
      "name": "search",
      "brief": "Semantic search across docs and code with filters. Returns relevant chunks with citations.",
      "category": "search",
      "use_cases": [
        "Find specific information in documentation",
        "Search code by function or class name",
        "Filter results by content type or language"
      ]
    }
  },
  "total_tools": 3,
  "tier": 1
}
```

**Token Usage**: ~30-50 tokens per tool (vs. 200-500 for full schema)

---

### Tier 2: Strategy-Specific Schemas (Loaded On-Demand)

**Purpose**: Full tool schema when a tool is selected

**Tool**: `get_tool_schema`

**Usage**: Call after selecting a tool from manifest

**Returns**:
- Complete tool description
- Full input schema with all parameters
- Example use cases
- Parameter types and constraints

**Example**:
```json
{
  "tool_name": "search",
  "tier": 2,
  "schema": {
    "name": "search",
    "description": "Semantic search across all project documentation...",
    "input_schema": {
      "type": "object",
      "properties": {
        "query": {...},
        "content_type": {...},
        "language": {...},
        "top_k": {...}
      }
    },
    "examples": [...]
  }
}
```

**Token Usage**: Full schema only when needed

---

### Tier 3: Execution (On-Demand)

**Purpose**: Actual tool execution

**Tools**: `search`, `ask`, `explain`

**Usage**: Call tool with parameters after loading schema

**Token Usage**: Only execution results, not schema definitions

---

## Implementation Details

### File Structure

```
rag-server/
├── lib/
│   ├── core/
│   │   └── tool_manifest.py      # Manifest system core
│   └── tools/
│       └── manifest.py            # Manifest tools (get_manifest, get_tool_schema)
├── server.py                      # MCP server with tiered loading
└── docs/
    └── CONTEXT_ENGINEERING.md     # This file
```

### Core Components

#### 1. `ToolManifest` Class (`lib/core/tool_manifest.py`)

Manages the three-tier system:

- **`TOOL_BRIEFS`**: Tier 1 briefs (always loaded)
- **`_tool_schemas`**: Tier 2 schemas (loaded on-demand)
- **`get_manifest()`**: Returns all briefs
- **`get_tool_schema()`**: Returns full schema for a tool
- **`register_tool_schema()`**: Registers schemas from tool definitions

#### 2. Manifest Tools (`lib/tools/manifest.py`)

Two MCP tools:

- **`get_manifest`**: Returns Tier 1 briefs
- **`get_tool_schema`**: Returns Tier 2 schema for a specific tool

#### 3. Server Integration (`server.py`)

- Registers manifest tools alongside RAG tools
- Auto-registers tool schemas on startup
- Validates brief token counts
- Logs tier information

---

## Usage Examples

### Example 1: Discovery Workflow

**Step 1**: Get manifest (Tier 1)
```python
# Call get_manifest tool
result = get_manifest()
# Returns lightweight briefs for all tools
```

**Step 2**: Select tool and get schema (Tier 2)
```python
# After reviewing manifest, select "search"
result = get_tool_schema(tool_name="search")
# Returns full schema with all parameters
```

**Step 3**: Execute tool (Tier 3)
```python
# Use the tool with full knowledge of parameters
result = search(
    query="authentication flow",
    content_type="doc",
    top_k=10
)
```

### Example 2: Direct Execution (Backward Compatible)

If you already know which tool to use, you can call it directly:

```python
# Direct execution (schema loaded automatically)
result = search(query="login function", content_type="code")
```

The server still supports traditional `list_tools()` which returns all tools, but using the manifest system is more efficient.

---

## Benefits

### 1. Reduced Context Usage

**Before** (Traditional):
- 3 tools × 300 tokens = 900 tokens upfront
- Most tools never used
- Context wasted

**After** (Context Engineering):
- 3 tools × 40 tokens (briefs) = 120 tokens upfront
- Load full schema only when needed
- **87% reduction** in initial context usage

### 2. Scalability

As more tools are added:
- Traditional: Context grows linearly (N tools × 300 tokens)
- Context Engineering: Context grows minimally (N tools × 40 tokens)

**Example**: 10 tools
- Traditional: 3,000 tokens
- Context Engineering: 400 tokens + on-demand schemas
- **87% reduction** even with 10 tools

### 3. Better Performance

- Faster initial tool discovery
- Reduced context window pressure
- AI assistants can process more information
- Better tool selection decisions

---

## Token Limits & Validation

### Brief Token Limits

Each tool brief is validated to stay within **30-50 tokens**:

```python
# Validation runs on server startup
validation = ToolManifest.validate_briefs()
# Returns token counts and validation status
```

### Token Estimation

Uses rough estimation: **1 token ≈ 4 characters**

This ensures briefs stay lightweight while providing enough information for tool selection.

---

## Integration with Agentic RAG

This context engineering system integrates with agentic RAG workflows:

1. **Strategy Selection**: AI uses manifest to discover available tools
2. **Tool Selection**: AI selects tools based on briefs
3. **Schema Loading**: Full schemas loaded only for selected tools
4. **Execution**: Tools executed with full parameter knowledge

This prevents context rot in multi-tool agentic systems.

---

## Configuration

### Adding New Tools

To add a new tool with context engineering:

1. **Add Tier 1 Brief** (`lib/core/tool_manifest.py`):
```python
TOOL_BRIEFS = {
    "new_tool": ToolBrief(
        name="new_tool",
        brief="Brief description (~30-50 tokens)",
        category="category",
        use_cases=["Use case 1", "Use case 2"]
    )
}
```

2. **Register Tier 2 Schema** (`server.py`):
```python
ToolManifest.register_tool_schema(
    "new_tool",
    tool_mcp.description,
    tool_mcp.inputSchema,
    examples=[...]
)
```

3. **Add Tool to Server** (`server.py`):
```python
ALL_TOOLS = [
    ...,
    new_tool_mcp
]
```

4. **Add Tool Handler** (`server.py`):
```python
elif name == "new_tool":
    result = new_tool(...)
```

---

## Monitoring & Logging

The server logs context engineering information:

```
INFO: Tool manifest validation:
INFO:   ✅ search: 42 tokens
INFO:   ✅ ask: 38 tokens
INFO:   ✅ explain: 35 tokens
INFO: Context Engineering: Three-tier system enabled
INFO:   Tier 1: get_manifest (lightweight briefs)
INFO:   Tier 2: get_tool_schema (on-demand schemas)
INFO:   Tier 3: Tool execution (search, ask, explain)
```

---

## Best Practices

### For AI Assistants

1. **Start with Manifest**: Always call `get_manifest` first
2. **Select Tools**: Choose tools based on briefs
3. **Load Schemas**: Get full schemas only for selected tools
4. **Execute**: Use tools with full parameter knowledge

### For Developers

1. **Keep Briefs Short**: 30-50 tokens maximum
2. **Clear Use Cases**: 2-3 specific use cases per tool
3. **Validate Tokens**: Check token counts on startup
4. **Update Examples**: Keep examples current and relevant

---

## Testing

### Manual Testing

1. **Test Manifest**:
```bash
# Call get_manifest tool
# Verify briefs are 30-50 tokens
# Verify all tools are listed
```

2. **Test Schema Loading**:
```bash
# Call get_tool_schema for each tool
# Verify full schemas are returned
# Verify examples are included
```

3. **Test Execution**:
```bash
# Execute tools after loading schemas
# Verify tools work correctly
# Verify backward compatibility
```

### Validation

The server automatically validates briefs on startup:
- Token counts checked
- Warnings for out-of-range briefs
- Logs validation results

---

## Future Enhancements

Potential improvements:

1. **Caching**: Cache loaded schemas to avoid re-loading
2. **Metrics**: Track which tools are used most
3. **Auto-briefing**: Generate briefs from tool descriptions
4. **Strategy Routing**: Route to tools based on query intent
5. **Lazy Loading**: Load schemas only when tool is first called

---

## References

- **Context Engineering Principles**: Based on MCP context engineering best practices
- **Token Optimization**: 30-50 token briefs prevent context rot
- **Agentic RAG**: Integrates with agentic RAG strategy selection
- **MCP Standards**: Follows MCP tool definition standards

---

## Summary

✅ **Three-tier context engineering implemented**  
✅ **87% reduction in initial context usage**  
✅ **Scalable to many tools**  
✅ **Backward compatible**  
✅ **Production ready**

The RAG server now supports efficient, scalable tool discovery and usage through progressive loading, preventing context rot and improving performance in agentic RAG systems.

