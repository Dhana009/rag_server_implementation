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

# Add rag-server to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, ListToolsRequest, ListToolsResult, CallToolRequest, CallToolResult
from lib.tools.search import search_tool, search_tool_mcp
from lib.tools.ask import ask_tool, ask_tool_mcp
from lib.tools.explain import explain_tool, explain_tool_mcp

# Configure logging to stderr AND file (MCP requires stdout for JSON-RPC only)
log_file = Path(__file__).parent / "rag-server.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.INFO)
stderr_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stderr_handler]  # Log to both file and stderr
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file}")

# Get server name from environment variable or use default
server_name = os.getenv("MCP_SERVER_NAME", "rag-server")

# Create MCP server
server = Server(server_name)

# All available tools - Core RAG tools only
ALL_TOOLS = [
    search_tool_mcp,
    ask_tool_mcp,
    explain_tool_mcp
]

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
    if name == "search":
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
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Stdio server started, waiting for connections...")
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

