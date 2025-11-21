#!/usr/bin/env python3
"""
Verify server starts correctly and lists all tools.

Checks:
1. Server can be imported
2. All expected tools are present
3. Old tools are removed
4. New QUADRANTDB tools are present
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.WARNING,  # Suppress INFO logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("="*60)
print("Verifying Server Tools")
print("="*60)

# Expected tools - ONLY QUADRANTDB tools
EXPECTED_QUADRANTDB_TOOLS = [
    "add_vector",
    "get_vector",
    "update_vector",
    "delete_vector",
    "search_similar",
    "search_by_metadata"
]

# Old tools that should NOT be present
OLD_TOOLS = [
    "add_points",
    "update_points",
    "delete_points",
    "get_points",
    "query_points",
    "add_document",
    "update_document",
    "delete_document",
    "get_document",
    "get_collection_stats"
]

try:
    # Import server
    print("\n[1] Importing server...")
    import server  # noqa: E402
    print("[OK] Server imported successfully")
    
    # Get all tools
    print("\n[2] Getting tool list...")
    all_tools = [tool.name for tool in server.ALL_TOOLS]
    print(f"[OK] Found {len(all_tools)} tools")
    
    # Check for expected tools
    print("\n[3] Verifying expected tools...")
    missing_tools = []
    
    for tool in EXPECTED_QUADRANTDB_TOOLS:
        if tool not in all_tools:
            missing_tools.append(tool)
            print(f"[FAIL] Missing: {tool}")
        else:
            print(f"[OK] Found: {tool}")
    
    # Check for old tools (should NOT be present)
    print("\n[4] Verifying old tools are removed...")
    found_old_tools = []
    
    for tool in OLD_TOOLS:
        if tool in all_tools:
            found_old_tools.append(tool)
            print(f"[FAIL] Old tool still present: {tool}")
        else:
            print(f"[OK] Old tool removed: {tool}")
    
    # Summary
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)
    
    if missing_tools:
        print(f"[FAIL] Missing {len(missing_tools)} expected tools: {', '.join(missing_tools)}")
    else:
        print("[OK] All expected tools present")
    
    if found_old_tools:
        print(f"[FAIL] Found {len(found_old_tools)} old tools that should be removed: {', '.join(found_old_tools)}")
    else:
        print("[OK] All old tools removed")
    
    # Check tool manifest
    print("\n[5] Verifying tool manifest...")
    from lib.core.tool_manifest import ToolManifest
    
    manifest = ToolManifest.get_manifest()
    manifest_tools = list(manifest.keys())
    
    print(f"[OK] Manifest has {len(manifest_tools)} tools")
    
    # Check QUADRANTDB tools in manifest
    quadrantdb_in_manifest = [t for t in EXPECTED_QUADRANTDB_TOOLS if t in manifest_tools]
    print(f"[OK] QUADRANTDB tools in manifest: {len(quadrantdb_in_manifest)}/{len(EXPECTED_QUADRANTDB_TOOLS)}")
    
    # Final result
    print("\n" + "="*60)
    if missing_tools or found_old_tools:
        print("[FAIL] VERIFICATION FAILED")
        print("="*60)
        sys.exit(1)
    else:
        print("[OK] VERIFICATION PASSED")
        print("="*60)
        print("\nAll tools verified successfully!")
        print(f"Total tools: {len(all_tools)}")
        print(f"  - QUADRANTDB tools: {len(EXPECTED_QUADRANTDB_TOOLS)}")
        print("\nOnly QUADRANTDB vector database tools are available.")
        sys.exit(0)
        
except Exception as e:
    print(f"\n❌ Verification failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

