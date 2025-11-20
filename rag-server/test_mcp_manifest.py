#!/usr/bin/env python3
"""Quick test of MCP manifest tools"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import server to register schemas
import server

from lib.tools.manifest import get_manifest_tool, get_tool_schema_tool

print("="*60)
print("Testing MCP Context Engineering Tools")
print("="*60)

# Test Tier 1: Get Manifest
print("\n[TEST 1] Calling get_manifest tool (Tier 1)...")
manifest_result = get_manifest_tool()
manifest_data = json.loads(manifest_result)

print(f"[OK] Manifest retrieved")
print(f"  Total tools: {manifest_data.get('total_tools')}")
print(f"  Tier: {manifest_data.get('tier')}")
print(f"  Tools available: {', '.join(manifest_data.get('manifest', {}).keys())}")

# Test Tier 2: Get Tool Schema
print("\n[TEST 2] Calling get_tool_schema tool for 'search' (Tier 2)...")
schema_result = get_tool_schema_tool("search")
schema_data = json.loads(schema_result)

if "error" not in schema_data:
    print(f"[OK] Schema retrieved")
    print(f"  Tool: {schema_data.get('tool_name')}")
    print(f"  Tier: {schema_data.get('tier')}")
    schema = schema_data.get('schema', {})
    print(f"  Has description: {bool(schema.get('description'))}")
    print(f"  Has input schema: {bool(schema.get('input_schema'))}")
    print(f"  Examples: {len(schema.get('examples', []))}")
else:
    print(f"[ERROR] Error: {schema_data.get('error')}")

print("\n" + "="*60)
print("MCP Tools are ready to use!")
print("="*60)
print("\nYou can now use these tools in Cursor:")
print("  - get_manifest: Get lightweight tool briefs")
print("  - get_tool_schema: Get full schema for a tool")
print("  - search, ask, explain: RAG tools")

