# Context Engineering - Quick Start Guide

## What is Context Engineering?

A three-tier system that prevents context rot by loading tool information progressively:
- **Tier 1**: Lightweight briefs (~30-50 tokens) - always loaded
- **Tier 2**: Full schemas - loaded on-demand when tool is selected
- **Tier 3**: Tool execution - on-demand when tool is called

## Quick Usage

### 1. Discover Available Tools

```python
# Call get_manifest to see all available tools
result = get_manifest()
# Returns: Brief descriptions of all tools (~30-50 tokens each)
```

### 2. Get Full Schema for a Tool

```python
# After selecting a tool, get its full schema
result = get_tool_schema(tool_name="search")
# Returns: Complete schema with all parameters and examples
```

### 3. Execute the Tool

```python
# Use the tool with full parameter knowledge
result = search(
    query="authentication flow",
    content_type="doc",
    top_k=10
)
```

## Available Tools

### Context Engineering Tools

- **`get_manifest`**: Get lightweight briefs for all tools (Tier 1)
- **`get_tool_schema`**: Get full schema for a specific tool (Tier 2)

### RAG Tools

- **`search`**: Semantic search across docs and code
- **`ask`**: Question-answering with full RAG pipeline
- **`explain`**: Comprehensive explanations with context

## Benefits

- ✅ **87% reduction** in initial context usage
- ✅ **Scalable** to many tools without context bloat
- ✅ **Backward compatible** - direct tool calls still work
- ✅ **Production ready** - prevents context rot

## Example Workflow

```python
# Step 1: Discover tools (Tier 1)
manifest = get_manifest()
# Returns briefs: search, ask, explain

# Step 2: Select tool and get schema (Tier 2)
schema = get_tool_schema(tool_name="search")
# Returns full schema with parameters

# Step 3: Execute tool (Tier 3)
results = search(query="login function", content_type="code")
# Returns search results
```

## Direct Execution (Backward Compatible)

You can still call tools directly without using the manifest:

```python
# Direct execution - schema loaded automatically
results = search(query="authentication", top_k=5)
```

## Token Savings

**Traditional Approach**:
- 3 tools × 300 tokens = **900 tokens** upfront

**Context Engineering**:
- 3 tools × 40 tokens (briefs) = **120 tokens** upfront
- Load full schema only when needed
- **87% reduction** in context usage

## For More Details

See [CONTEXT_ENGINEERING.md](./CONTEXT_ENGINEERING.md) for complete documentation.

