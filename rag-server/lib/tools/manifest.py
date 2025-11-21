"""
Manifest Tools - Context Engineering Optimization

Provides tools for three-tier context engineering:
- get_manifest: Returns lightweight tool briefs (Tier 1)
- get_tool_schema: Returns full schema for a specific tool (Tier 2)
"""

import json
import logging
from mcp.types import Tool
from lib.core.tool_manifest import ToolManifest

logger = logging.getLogger(__name__)

def get_manifest_tool() -> str:
    """
    Get Tier 1 manifest - lightweight briefs for all tools.
    Returns minimal information (~30-50 tokens per tool) to prevent context rot.
    
    Returns:
        JSON string with tool briefs
    """
    try:
        manifest = ToolManifest.get_manifest()
        validation = ToolManifest.validate_briefs()
        
        result = {
            "manifest": manifest,
            "validation": validation,
            "total_tools": len(manifest),
            "tier": 1,
            "description": "Lightweight tool briefs for initial discovery. Use get_tool_schema for full details."
        }
        
        logger.info(f"Manifest requested: {len(manifest)} tools")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting manifest: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

def get_tool_schema_tool(tool_name: str) -> str:
    """
    Get Tier 2 schema for a specific tool (loaded on-demand).
    Returns full schema including description, input schema, and examples.
    
    Args:
        tool_name: Name of the tool to get schema for
        
    Returns:
        JSON string with full tool schema
    """
    try:
        schema = ToolManifest.get_tool_schema(tool_name)
        if not schema:
            # Try to get brief as fallback
            brief = ToolManifest.get_tool_brief(tool_name)
            if brief:
                return json.dumps({
                    "tool_name": tool_name,
                    "tier": 1,
                    "brief": brief,
                    "message": "Full schema not yet registered. Brief information available.",
                    "note": "Tool schema will be loaded when tool is first used."
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(ToolManifest.TOOL_BRIEFS.keys())
                }, indent=2)
        
        logger.info(f"Tool schema requested: {tool_name}")
        return json.dumps({
            "tool_name": tool_name,
            "tier": 2,
            "schema": schema
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting tool schema: {tool_name}: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

# MCP Tool definitions
get_manifest_tool_mcp = Tool(
    name="get_manifest",
    description="Get lightweight tool manifest (Tier 1). Returns brief descriptions (~30-50 tokens each) for all available tools. Use this for initial tool discovery to avoid context rot.",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
)

get_tool_schema_tool_mcp = Tool(
    name="get_tool_schema",
    description="Get full schema for a specific tool (Tier 2). Loads complete tool definition on-demand. Use after selecting a tool from the manifest.",
    inputSchema={
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to get schema for",
                "enum": [
                    "add_vector", "get_vector", "update_vector", "delete_vector",
                    "search_similar", "search_by_metadata"
                ]
            }
        },
        "required": ["tool_name"]
    }
)

