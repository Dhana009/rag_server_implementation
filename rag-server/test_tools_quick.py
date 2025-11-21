#!/usr/bin/env python3
"""
Quick test - Verify all 6 QUADRANTDB tools are registered correctly.
Tests tool registration without requiring database connection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("QUADRANTDB Tools - Quick Registration Test")
print("="*70)

try:
    # Import server
    import server
    print("\n[OK] Server imported successfully")
    
    # Get all tools
    all_tools = [tool.name for tool in server.ALL_TOOLS]
    print(f"[OK] Found {len(all_tools)} tools")
    
    # Expected QUADRANTDB tools
    expected_tools = [
        "add_vector",
        "get_vector", 
        "update_vector",
        "delete_vector",
        "search_similar",
        "search_by_metadata"
    ]
    
    print("\n" + "="*70)
    print("Tool Registration Check")
    print("="*70)
    
    all_present = True
    for tool in expected_tools:
        if tool in all_tools:
            print(f"[OK] {tool} - Registered")
        else:
            print(f"[FAIL] {tool} - MISSING")
            all_present = False
    
    # Check for unexpected tools
    unexpected = [t for t in all_tools if t not in expected_tools]
    if unexpected:
        print(f"\n[WARN] Unexpected tools found: {unexpected}")
        all_present = False
    
    print("\n" + "="*70)
    if all_present and len(all_tools) == 6:
        print("[OK] ALL TESTS PASSED")
        print("="*70)
        print("\nAll 6 QUADRANTDB tools are correctly registered!")
        print(f"Total tools: {len(all_tools)}")
        print("\nTools available:")
        for tool in expected_tools:
            print(f"  - {tool}")
        print("\n[OK] Ready to use in Cursor MCP!")
        sys.exit(0)
    else:
        print("[FAIL] TESTS FAILED")
        print("="*70)
        print(f"Expected 6 tools, found {len(all_tools)}")
        if unexpected:
            print(f"Unexpected tools: {unexpected}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

