#!/usr/bin/env python3
"""
Test all 7 QUADRANTDB MCP tools directly.
Tests each tool to verify they work correctly.
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Set environment
os.environ["MCP_ENV_FILE"] = str(Path(__file__).parent / ".env.qdrant")

from lib.tools.vector_crud import (
    add_vector, get_vector, update_vector, delete_vector,
    search_similar, search_by_metadata, index_repository
)

def test_add_vector():
    """Test add_vector tool"""
    print("\n" + "="*70)
    print("[TEST 1] add_vector - Adding test data")
    print("="*70)
    
    result = add_vector(
        content="This is test data for MCP tool verification",
        metadata={"category": "test", "type": "mcp_test", "file_path": "test_mcp.py"}
    )
    data = json.loads(result)
    
    if data["success"]:
        vector_id = data["data"]["vector_id"]
        print(f"[OK] add_vector: SUCCESS")
        print(f"   Vector ID: {vector_id}")
        return vector_id
    else:
        print(f"[FAIL] add_vector: FAILED")
        print(f"   Error: {data['errors']}")
        return None

def test_get_vector(vector_id):
    """Test get_vector tool"""
    print("\n" + "="*70)
    print("[TEST 2] get_vector - Retrieving vector by ID")
    print("="*70)
    
    if not vector_id:
        print("[SKIP] No vector_id available")
        return False
    
    result = get_vector(vector_id, include_vector=False)
    data = json.loads(result)
    
    if data["success"]:
        print(f"[OK] get_vector: SUCCESS")
        print(f"   Vector ID: {data['data']['vector_id']}")
        print(f"   Metadata: {list(data['data']['metadata'].keys())}")
        return True
    else:
        print(f"[FAIL] get_vector: FAILED")
        print(f"   Error: {data['errors']}")
        return False

def test_update_vector(vector_id):
    """Test update_vector tool"""
    print("\n" + "="*70)
    print("[TEST 3] update_vector - Updating vector content and metadata")
    print("="*70)
    
    if not vector_id:
        print("[SKIP] No vector_id available")
        return False
    
    result = update_vector(
        vector_id=vector_id,
        content="Updated test data for MCP tool verification - MODIFIED",
        metadata={"status": "updated", "tested": True}
    )
    data = json.loads(result)
    
    if data["success"]:
        print(f"[OK] update_vector: SUCCESS")
        print(f"   Updated metadata keys: {list(data['data']['metadata'].keys())}")
        return True
    else:
        print(f"[FAIL] update_vector: FAILED")
        print(f"   Error: {data['errors']}")
        return False

def test_search_similar():
    """Test search_similar tool"""
    print("\n" + "="*70)
    print("[TEST 4] search_similar - Semantic similarity search")
    print("="*70)
    
    result = search_similar(
        query="MCP tool verification test data",
        top_k=5
    )
    data = json.loads(result)
    
    if data["success"]:
        count = data["data"]["count"]
        print(f"[OK] search_similar: SUCCESS")
        print(f"   Found {count} results")
        if count > 0:
            top_result = data["data"]["results"][0]
            print(f"   Top result ID: {top_result['vector_id']}")
            print(f"   Top result score: {top_result['score']:.4f}")
        return True
    else:
        print(f"[FAIL] search_similar: FAILED")
        print(f"   Error: {data['errors']}")
        return False

def test_search_by_metadata():
    """Test search_by_metadata tool"""
    print("\n" + "="*70)
    print("[TEST 5] search_by_metadata - Filter by metadata")
    print("="*70)
    
    # Try with file_path which is more likely to work without index
    result = search_by_metadata(
        filter={"must": [{"key": "file_path", "match": "test_mcp.py"}]},
        limit=10
    )
    data = json.loads(result)
    
    if data["success"]:
        count = data["data"]["count"]
        print(f"[OK] search_by_metadata: SUCCESS")
        print(f"   Found {count} results with file_path='test_mcp.py'")
        if count > 0:
            print(f"   Note: search_by_metadata works but requires Qdrant indexes for some fields")
        return True
    else:
        # If file_path doesn't work, try without filter (just get any results)
        print(f"[WARN] search_by_metadata with filter failed (may need Qdrant index)")
        print(f"   Error: {data['errors'][0]['message'][:100]}...")
        print(f"   Note: This is a Qdrant configuration issue, not a tool issue")
        print(f"   The tool works, but Qdrant needs indexes created for filtered fields")
        return False

def test_index_repository():
    """Test index_repository tool"""
    print("\n" + "="*70)
    print("[TEST 6] index_repository - Index entire repository")
    print("="*70)
    
    # Index just the rag-server directory for testing
    repo_path = Path(__file__).parent
    result = index_repository(
        repository_path=str(repo_path),
        index_docs=True,
        index_code=False,  # Skip code to make it faster
        collection="cloud"
    )
    data = json.loads(result)
    
    if data["success"]:
        result_data = data["data"]
        print(f"[OK] index_repository: SUCCESS")
        print(f"   Repository: {result_data['repository_path']}")
        print(f"   Docs indexed: {result_data['docs_indexed']} chunks")
        print(f"   Code indexed: {result_data['code_indexed']} files")
        print(f"   Errors: {result_data['errors']}")
        print(f"   Cleanup deleted: {result_data.get('cleanup_deleted', 0)} chunks")
        return True
    else:
        print(f"[FAIL] index_repository: FAILED")
        print(f"   Error: {data['errors']}")
        return False

def test_delete_vector(vector_id):
    """Test delete_vector tool"""
    print("\n" + "="*70)
    print("[TEST 7] delete_vector - Delete vector (soft delete)")
    print("="*70)
    
    if not vector_id:
        print("[SKIP] No vector_id available")
        return False
    
    result = delete_vector(vector_id, soft_delete=True)
    data = json.loads(result)
    
    if data["success"]:
        print(f"[OK] delete_vector: SUCCESS")
        print(f"   Deleted vector ID: {data['data']['vector_id']}")
        print(f"   Soft delete: True (recoverable)")
        return True
    else:
        print(f"[FAIL] delete_vector: FAILED")
        print(f"   Error: {data['errors']}")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("QUADRANTDB MCP Tools - Complete Test Suite")
    print("="*70)
    print("\nTesting all 7 QUADRANTDB tools:")
    print("  1. add_vector")
    print("  2. get_vector")
    print("  3. update_vector")
    print("  4. search_similar")
    print("  5. search_by_metadata")
    print("  6. index_repository")
    print("  7. delete_vector")
    
    results = {}
    vector_id = None
    
    # Test 1: add_vector
    vector_id = test_add_vector()
    results["add_vector"] = vector_id is not None
    
    # Test 2: get_vector
    results["get_vector"] = test_get_vector(vector_id)
    
    # Test 3: update_vector
    results["update_vector"] = test_update_vector(vector_id)
    
    # Test 4: search_similar
    results["search_similar"] = test_search_similar()
    
    # Test 5: search_by_metadata
    results["search_by_metadata"] = test_search_by_metadata()
    
    # Test 6: index_repository
    results["index_repository"] = test_index_repository()
    
    # Test 7: delete_vector
    results["delete_vector"] = test_delete_vector(vector_id)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for tool_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {tool_name}")
    
    print(f"\n[PASS] Passed: {passed}/{total}")
    print(f"[FAIL] Failed: {total - passed}/{total}")
    print(f"[INFO] Success Rate: {passed / total * 100:.1f}%")
    print("="*70 + "\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

