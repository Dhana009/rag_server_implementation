#!/usr/bin/env python3
"""
List all available tools in the MCP server with clear categorization.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import server

print("="*70)
print("RAG Server MCP - All Available Tools")
print("="*70)

all_tools = [tool.name for tool in server.ALL_TOOLS]

# Categorize tools
core_rag_tools = ["search", "ask", "explain"]
context_tools = ["get_manifest", "get_tool_schema"]
quadrantdb_tools = ["add_vector", "get_vector", "update_vector", "delete_vector", 
                    "search_similar", "search_by_metadata"]

print(f"\nTotal Tools: {len(all_tools)}\n")

print("="*70)
print("1. CONTEXT ENGINEERING TOOLS (2 tools)")
print("="*70)
for tool in context_tools:
    if tool in all_tools:
        print(f"  [OK] {tool}")
    else:
        print(f"  [MISSING] {tool}")

print("\n" + "="*70)
print("2. CORE RAG TOOLS (3 tools)")
print("="*70)
for tool in core_rag_tools:
    if tool in all_tools:
        print(f"  [OK] {tool}")
    else:
        print(f"  [MISSING] {tool}")

print("\n" + "="*70)
print("3. QUADRANTDB TOOLS - Vector Database (6 tools)")
print("="*70)
for tool in quadrantdb_tools:
    if tool in all_tools:
        print(f"  [OK] {tool}")
    else:
        print(f"  [MISSING] {tool}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"  Context Engineering: {len([t for t in context_tools if t in all_tools])}/2")
print(f"  Core RAG:            {len([t for t in core_rag_tools if t in all_tools])}/3")
print(f"  QUADRANTDB:          {len([t for t in quadrantdb_tools if t in all_tools])}/6")
print(f"  TOTAL:               {len(all_tools)}/11")
print("="*70)

# Check for any unexpected tools
expected_all = set(context_tools + core_rag_tools + quadrantdb_tools)
actual_all = set(all_tools)
unexpected = actual_all - expected_all
missing = expected_all - actual_all

if unexpected:
    print(f"\n[WARN] UNEXPECTED TOOLS FOUND: {unexpected}")
if missing:
    print(f"\n[WARN] MISSING EXPECTED TOOLS: {missing}")

if not unexpected and not missing:
    print("\n[OK] All tools are correct! 11 tools total is EXPECTED.")
    print("   - 2 Context Engineering tools")
    print("   - 3 Core RAG tools")
    print("   - 6 QUADRANTDB tools")
    print("\n   All old vector CRUD tools have been removed.")
    print("\n   This is the correct number of tools!")

print("="*70)
