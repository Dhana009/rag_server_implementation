#!/usr/bin/env python3
"""
MCP Server - QUADRANTDB Vector Database Tools

Provides 6 core vector database operations:
- add_vector: Store new data with embeddings + metadata
- get_vector: Retrieve a stored vector item by ID
- update_vector: Update text/metadata for an existing vector entry
- delete_vector: Delete a stored vector entry
- search_similar: Semantic similarity search using embeddings
- search_by_metadata: Retrieve items by tags/category/file/error-type, etc.
"""

import logging
import os
import sys
from pathlib import Path

# Suppress tqdm progress bars (they clutter stderr in MCP servers)
# Set environment variable to disable tqdm output
os.environ['TQDM_DISABLE'] = '1'

# Import mcp BEFORE adding current directory to path (to avoid conflict with local files)
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, ListToolsRequest, ListToolsResult, CallToolRequest, CallToolResult

# Add rag-server to path (after mcp imports to avoid shadowing)
sys.path.insert(0, str(Path(__file__).parent))
# Removed: search, ask, explain, get_manifest, get_tool_schema
# Only QUADRANTDB tools remain
from lib.tools.vector_crud import (
    add_vector, get_vector, update_vector, delete_vector,
    search_similar, search_by_metadata,
    add_vector_tool_mcp, get_vector_tool_mcp, update_vector_tool_mcp,
    delete_vector_tool_mcp, search_similar_tool_mcp, search_by_metadata_tool_mcp
)
from lib.core.tool_manifest import ToolManifest

# Configure logging: INFO to file, WARNING/ERROR to stderr (MCP requires stdout for JSON-RPC only)
log_file = Path(__file__).parent / "rag-server.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)  # Log everything to file
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Only log WARNING and above to stderr to avoid cluttering Cursor's error panel
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)  # Only warnings and errors to stderr
stderr_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.DEBUG,  # Capture everything
    handlers=[file_handler, stderr_handler]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file} (INFO+ to file, WARNING+ to stderr)")

# Get server name from environment variable or use default
server_name = os.getenv("MCP_SERVER_NAME", "rag-server")

# Create MCP server
server = Server(server_name)

# All available tools - QUADRANTDB tools only (6 tools)
ALL_TOOLS = [
    # QUADRANTDB tools (vector database)
    add_vector_tool_mcp,
    get_vector_tool_mcp,
    update_vector_tool_mcp,
    delete_vector_tool_mcp,
    search_similar_tool_mcp,
    search_by_metadata_tool_mcp
]

# Register QUADRANTDB tool schemas only
ToolManifest.register_tool_schema(
    "add_vector",
    add_vector_tool_mcp.description,
    add_vector_tool_mcp.inputSchema,
    examples=[
        {"content": "Test data for QA", "metadata": {"category": "test", "file_path": "test.md"}},
        {"content": "Error log entry", "metadata": {"error_type": "timeout", "severity": "high"}},
        {"vector": [0.1]*384, "metadata": {"custom": "data"}}
    ]
)

ToolManifest.register_tool_schema(
    "get_vector",
    get_vector_tool_mcp.description,
    get_vector_tool_mcp.inputSchema,
    examples=[
        {"vector_id": 12345},
        {"vector_id": 12345, "include_vector": True}
    ]
)

ToolManifest.register_tool_schema(
    "update_vector",
    update_vector_tool_mcp.description,
    update_vector_tool_mcp.inputSchema,
    examples=[
        {"vector_id": 12345, "content": "Updated content"},
        {"vector_id": 12345, "metadata": {"category": "updated"}},
        {"vector_id": 12345, "content": "New content", "metadata": {"updated": True}}
    ]
)

ToolManifest.register_tool_schema(
    "delete_vector",
    delete_vector_tool_mcp.description,
    delete_vector_tool_mcp.inputSchema,
    examples=[
        {"vector_id": 12345, "soft_delete": True},
        {"vector_id": 12345, "soft_delete": False}
    ]
)

ToolManifest.register_tool_schema(
    "search_similar",
    search_similar_tool_mcp.description,
    search_similar_tool_mcp.inputSchema,
    examples=[
        {"query": "authentication error", "top_k": 10},
        {"query": "test data", "top_k": 5, "filter": {"must": [{"key": "category", "match": "test"}]}}
    ]
)

ToolManifest.register_tool_schema(
    "search_by_metadata",
    search_by_metadata_tool_mcp.description,
    search_by_metadata_tool_mcp.inputSchema,
    examples=[
        {"filter": {"must": [{"key": "category", "match": "error"}]}, "limit": 10},
        {"filter": {"must": [{"key": "file_path", "match": "test.py"}]}, "limit": 20, "offset": 0}
    ]
)

# Register tools using decorator
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    logger.info(f"ListToolsRequest received, returning {len(ALL_TOOLS)} tools")
    return ALL_TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> dict:
    """Handle tool calls"""
    logger.info(f"Tool call received: {name} with args: {arguments}")
    
    # QUADRANTDB tools (vector database) - only tools available
    if name == "add_vector":
        content = arguments.get("content", "")
        metadata = arguments.get("metadata", {})
        vector = arguments.get("vector")
        result = add_vector(content, metadata, vector)
    elif name == "get_vector":
        vector_id = arguments.get("vector_id")
        include_vector = arguments.get("include_vector", False)
        result = get_vector(vector_id, include_vector)
    elif name == "update_vector":
        vector_id = arguments.get("vector_id")
        content = arguments.get("content")
        metadata = arguments.get("metadata")
        vector = arguments.get("vector")
        result = update_vector(vector_id, content, metadata, vector)
    elif name == "delete_vector":
        vector_id = arguments.get("vector_id")
        soft_delete = arguments.get("soft_delete", False)
        result = delete_vector(vector_id, soft_delete)
    elif name == "search_similar":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 10)
        vector = arguments.get("vector")
        filter_dict = arguments.get("filter")
        result = search_similar(query, top_k, vector, filter_dict)
    elif name == "search_by_metadata":
        filter_dict = arguments.get("filter", {})
        limit = arguments.get("limit", 10)
        offset = arguments.get("offset", 0)
        result = search_by_metadata(filter_dict, limit, offset)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    return {
        "content": [
            {
                "type": "text",
                "text": result
            }
        ]
    }

async def main():
    """Main entry point"""
    try:
        logger.info(f"Starting MCP Server ({server_name})...")
        logger.info(f"Server name: {server.name}")
        logger.info(f"Available tools: {len(ALL_TOOLS)}")
        
        # Validate tool briefs are within token limits
        validation = ToolManifest.validate_briefs()
        logger.info("Tool manifest validation:")
        for tool_name, result in validation.items():
            status = "✅" if result["within_limit"] else "⚠️"
            logger.info(f"  {status} {tool_name}: {result['tokens']} tokens")
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Stdio server started, waiting for connections...")
            logger.info("QUADRANTDB Tools: 6 vector database operations available")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

