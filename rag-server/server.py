#!/usr/bin/env python3
"""
MCP Server - RAG System
Provides intelligent access to project documentation and code via RAG (Retrieval-Augmented Generation)

Core Tools:
- search: Semantic search with filtering
- ask: Question answering with full RAG pipeline
- explain: Comprehensive explanations with context
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
from lib.tools.search import search_tool, search_tool_mcp
from lib.tools.ask import ask_tool, ask_tool_mcp
from lib.tools.explain import explain_tool, explain_tool_mcp
from lib.tools.manifest import get_manifest_tool, get_tool_schema_tool, get_manifest_tool_mcp, get_tool_schema_tool_mcp
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

# All available tools - Core RAG tools + Context Engineering tools
ALL_TOOLS = [
    # Context Engineering tools (Tier 1 & 2)
    get_manifest_tool_mcp,
    get_tool_schema_tool_mcp,
    # Core RAG tools (Tier 3 - execution)
    search_tool_mcp,
    ask_tool_mcp,
    explain_tool_mcp
]

# Register tool schemas in manifest system (Tier 2)
# This allows on-demand schema loading
ToolManifest.register_tool_schema(
    "search",
    search_tool_mcp.description,
    search_tool_mcp.inputSchema,
    examples=[
        {"query": "selector policy", "content_type": "doc"},
        {"query": "login function", "content_type": "code", "language": "python"},
        {"query": "authentication flow", "top_k": 5}
    ]
)

ToolManifest.register_tool_schema(
    "ask",
    ask_tool_mcp.description,
    ask_tool_mcp.inputSchema,
    examples=[
        {"question": "What is the selector policy?", "context": ""},
        {"question": "Should I use aria-label or aria-labelledby?", "context": "accessibility question"},
        {"question": "What's the difference between v1 and v2 UI?"}
    ]
)

ToolManifest.register_tool_schema(
    "explain",
    explain_tool_mcp.description,
    explain_tool_mcp.inputSchema,
    examples=[
        {"topic": "phase-1 flows"},
        {"topic": "selector policy"},
        {"topic": "architecture rules"},
        {"topic": "authentication flow"}
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
    
    # Context Engineering tools (Tier 1 & 2)
    if name == "get_manifest":
        result = get_manifest_tool()
    elif name == "get_tool_schema":
        tool_name = arguments.get("tool_name", "")
        result = get_tool_schema_tool(tool_name)
    # Core RAG tools (Tier 3 - execution)
    elif name == "search":
        query = arguments.get("query", "")
        content_type = arguments.get("content_type", "all")
        language = arguments.get("language", "all")
        top_k = arguments.get("top_k", 10)
        result = search_tool(query, content_type, language, top_k)
    elif name == "ask":
        question = arguments.get("question", "")
        context = arguments.get("context", "")
        result = ask_tool(question, context)
    elif name == "explain":
        topic = arguments.get("topic", "")
        result = explain_tool(topic)
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
            logger.info("Context Engineering: Three-tier system enabled")
            logger.info("  Tier 1: get_manifest (lightweight briefs)")
            logger.info("  Tier 2: get_tool_schema (on-demand schemas)")
            logger.info("  Tier 3: Tool execution (search, ask, explain)")
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

