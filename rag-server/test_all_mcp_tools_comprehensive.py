#!/usr/bin/env python3
"""
Comprehensive test for all 7 QUADRANTDB MCP tools - All parameters and edge cases.
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ["MCP_ENV_FILE"] = str(Path(__file__).parent / ".env.qdrant")

from lib.tools.vector_crud import (
    add_vector, get_vector, update_vector, delete_vector,
    search_similar, search_by_metadata, index_repository
)

def test_add_vector_all_variants():
    """Test add_vector with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 1] add_vector - All variants")
    print("="*70)
    
    results = {}
    
    # Test 1.1: With content only
    result1 = add_vector(
        content="Test content for variant 1",
        metadata={"variant": "content_only"}
    )
    data1 = json.loads(result1)
    results["content_only"] = data1["success"]
    vid1 = data1.get("data", {}).get("vector_id") if data1["success"] else None
    status1_1 = '[OK]' if results['content_only'] else '[FAIL]'
    print(f"  1.1 Content only: {status1_1}")
    
    # Test 1.2: With content + metadata
    result2 = add_vector(
        content="Test content for variant 2",
        metadata={"variant": "content_metadata", "category": "test"}
    )
    data2 = json.loads(result2)
    results["content_metadata"] = data2["success"]
    vid2 = data2.get("data", {}).get("vector_id") if data2["success"] else None
    status1_2 = '[OK]' if results['content_metadata'] else '[FAIL]'
    print(f"  1.2 Content + metadata: {status1_2}")
    
    # Test 1.3: With pre-computed vector (384 dimensions)
    test_vector = [0.1] * 384
    result3 = add_vector(
        vector=test_vector,
        metadata={"variant": "precomputed_vector"}
    )
    data3 = json.loads(result3)
    results["precomputed_vector"] = data3["success"]
    vid3 = data3.get("data", {}).get("vector_id") if data3["success"] else None
    status1_3 = '[OK]' if results['precomputed_vector'] else '[FAIL]'
    print(f"  1.3 Pre-computed vector: {status1_3}")
    
    return vid2, results

def test_get_vector_all_variants(vector_id):
    """Test get_vector with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 2] get_vector - All variants")
    print("="*70)
    
    if not vector_id:
        print("  [SKIP] No vector_id available")
        return {}
    
    results = {}
    
    # Test 2.1: Without vector (default)
    result1 = get_vector(vector_id, include_vector=False)
    data1 = json.loads(result1)
    results["without_vector"] = data1["success"]
    status2_1 = '[OK]' if results['without_vector'] else '[FAIL]'
    print(f"  2.1 Without vector: {status2_1}")
    
    # Test 2.2: With vector included
    result2 = get_vector(vector_id, include_vector=True)
    data2 = json.loads(result2)
    results["with_vector"] = data2["success"]
    has_vector = "vector" in data2.get("data", {}) if data2["success"] else False
    status2_2 = '[OK]' if results['with_vector'] and has_vector else '[FAIL]'
    print(f"  2.2 With vector: {status2_2}")
    
    return results

def test_update_vector_all_variants(vector_id):
    """Test update_vector with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 3] update_vector - All variants")
    print("="*70)
    
    if not vector_id:
        print("  [SKIP] No vector_id available")
        return {}
    
    results = {}
    
    # Test 3.1: Update content only
    result1 = update_vector(
        vector_id=vector_id,
        content="Updated content - variant 1"
    )
    data1 = json.loads(result1)
    results["content_only"] = data1["success"]
    status3_1 = '[OK]' if results['content_only'] else '[FAIL]'
    print(f"  3.1 Content only: {status3_1}")
    
    # Test 3.2: Update metadata only
    result2 = update_vector(
        vector_id=vector_id,
        metadata={"updated": True, "variant": "metadata_only"}
    )
    data2 = json.loads(result2)
    results["metadata_only"] = data2["success"]
    status3_2 = '[OK]' if results['metadata_only'] else '[FAIL]'
    print(f"  3.2 Metadata only: {status3_2}")
    
    # Test 3.3: Update both content and metadata
    result3 = update_vector(
        vector_id=vector_id,
        content="Updated content - variant 3",
        metadata={"variant": "both", "final": True}
    )
    data3 = json.loads(result3)
    results["both"] = data3["success"]
    status3_3 = '[OK]' if results['both'] else '[FAIL]'
    print(f"  3.3 Content + metadata: {status3_3}")
    
    return results

def test_search_similar_all_variants():
    """Test search_similar with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 4] search_similar - All variants")
    print("="*70)
    
    results = {}
    
    # Test 4.1: Basic search with query
    result1 = search_similar(query="test data", top_k=5)
    data1 = json.loads(result1)
    results["basic_query"] = data1["success"]
    status4_1 = '[OK]' if results['basic_query'] else '[FAIL]'
    print(f"  4.1 Basic query: {status4_1} - Found {data1.get('data', {}).get('count', 0)} results")
    
    # Test 4.2: Search with filter
    result2 = search_similar(
        query="test",
        top_k=5,
        filter={"must": [{"key": "file_path", "match": "test"}]}
    )
    data2 = json.loads(result2)
    results["with_filter"] = data2["success"]
    status4_2 = '[OK]' if results['with_filter'] else '[FAIL]'
    print(f"  4.2 With filter: {status4_2} - Found {data2.get('data', {}).get('count', 0)} results")
    
    # Test 4.3: Search with custom top_k
    result3 = search_similar(query="test", top_k=3)
    data3 = json.loads(result3)
    results["custom_top_k"] = data3["success"]
    count3 = data3.get("data", {}).get("count", 0)
    status4_3 = '[OK]' if results['custom_top_k'] and count3 <= 3 else '[FAIL]'
    print(f"  4.3 Custom top_k=3: {status4_3} - Found {count3} results")
    
    return results

def test_search_by_metadata_all_variants():
    """Test search_by_metadata with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 5] search_by_metadata - All variants")
    print("="*70)
    
    results = {}
    
    # Test 5.1: Basic filter
    result1 = search_by_metadata(
        filter={"must": [{"key": "file_path", "match": "test"}]},
        limit=10
    )
    data1 = json.loads(result1)
    results["basic_filter"] = data1["success"]
    status5_1 = '[OK]' if results['basic_filter'] else '[FAIL]'
    print(f"  5.1 Basic filter: {status5_1} - Found {data1.get('data', {}).get('count', 0)} results")
    
    # Test 5.2: With pagination (offset)
    result2 = search_by_metadata(
        filter={"must": [{"key": "file_path", "match": "test"}]},
        limit=5,
        offset=0
    )
    data2 = json.loads(result2)
    results["with_offset"] = data2["success"]
    status5_2 = '[OK]' if results['with_offset'] else '[FAIL]'
    print(f"  5.2 With offset=0: {status5_2} - Found {data2.get('data', {}).get('count', 0)} results")
    
    # Test 5.3: Custom limit
    result3 = search_by_metadata(
        filter={"must": [{"key": "file_path", "match": "test"}]},
        limit=20
    )
    data3 = json.loads(result3)
    results["custom_limit"] = data3["success"]
    status5_3 = '[OK]' if results['custom_limit'] else '[FAIL]'
    print(f"  5.3 Custom limit=20: {status5_3} - Found {data3.get('data', {}).get('count', 0)} results")
    
    return results

def test_index_repository_all_variants():
    """Test index_repository with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 6] index_repository - All variants")
    print("="*70)
    
    results = {}
    repo_path = Path(__file__).parent
    
    # Test 6.1: Docs only, cloud collection
    result1 = index_repository(
        repository_path=str(repo_path),
        index_docs=True,
        index_code=False,
        collection="cloud"
    )
    data1 = json.loads(result1)
    results["docs_cloud"] = data1["success"]
    status1 = '[OK]' if results['docs_cloud'] else '[FAIL]'
    print(f"  6.1 Docs only, cloud: {status1} - {data1.get('data', {}).get('docs_indexed', 0)} chunks")
    
    # Test 6.2: Docs + code, both collections
    result2 = index_repository(
        repository_path=str(repo_path),
        index_docs=True,
        index_code=True,
        collection="both"
    )
    data2 = json.loads(result2)
    results["docs_code_both"] = data2["success"]
    status2 = '[OK]' if results['docs_code_both'] else '[FAIL]'
    print(f"  6.2 Docs + code, both: {status2} - Docs: {data2.get('data', {}).get('docs_indexed', 0)}, Code: {data2.get('data', {}).get('code_indexed', 0)}")
    
    # Test 6.3: Custom patterns
    result3 = index_repository(
        repository_path=str(repo_path),
        index_docs=True,
        index_code=False,
        collection="cloud",
        doc_patterns=["*.md"]
    )
    data3 = json.loads(result3)
    results["custom_patterns"] = data3["success"]
    status3 = '[OK]' if results['custom_patterns'] else '[FAIL]'
    print(f"  6.3 Custom patterns: {status3} - {data3.get('data', {}).get('docs_indexed', 0)} chunks")
    
    return results

def test_delete_vector_all_variants(vector_id):
    """Test delete_vector with all parameter combinations"""
    print("\n" + "="*70)
    print("[TEST 7] delete_vector - All variants")
    print("="*70)
    
    if not vector_id:
        print("  [SKIP] No vector_id available")
        return {}
    
    results = {}
    
    # Create a new vector for testing
    result_add = add_vector(
        content="Test vector for delete testing",
        metadata={"test": "delete"}
    )
    data_add = json.loads(result_add)
    test_vid = data_add.get("data", {}).get("vector_id") if data_add["success"] else None
    
    if not test_vid:
        print("  [SKIP] Could not create test vector")
        return {}
    
    # Test 7.1: Soft delete
    result1 = delete_vector(test_vid, soft_delete=True)
    data1 = json.loads(result1)
    results["soft_delete"] = data1["success"]
    status_del1 = '[OK]' if results['soft_delete'] else '[FAIL]'
    print(f"  7.1 Soft delete: {status_del1}")
    
    # Verify it's soft-deleted (can still retrieve)
    result_check = get_vector(test_vid, include_vector=False)
    data_check = json.loads(result_check)
    is_deleted = data_check.get("data", {}).get("metadata", {}).get("is_deleted", False) if data_check["success"] else False
    status_soft = '[OK]' if is_deleted else '[FAIL]'
    print(f"      Verified soft-deleted: {status_soft}")
    
    # Test 7.2: Hard delete (create another vector)
    result_add2 = add_vector(
        content="Test vector for hard delete",
        metadata={"test": "hard_delete"}
    )
    data_add2 = json.loads(result_add2)
    test_vid2 = data_add2.get("data", {}).get("vector_id") if data_add2["success"] else None
    
    if test_vid2:
        result2 = delete_vector(test_vid2, soft_delete=False)
        data2 = json.loads(result2)
        results["hard_delete"] = data2["success"]
        status_del2 = '[OK]' if results['hard_delete'] else '[FAIL]'
        print(f"  7.2 Hard delete: {status_del2}")
        
        # Verify it's hard-deleted (cannot retrieve)
        result_check2 = get_vector(test_vid2, include_vector=False)
        data_check2 = json.loads(result_check2)
        hard_deleted = not data_check2["success"]  # Should fail to retrieve
        status_hard = '[OK]' if hard_deleted else '[FAIL]'
        print(f"      Verified hard-deleted: {status_hard}")
    
    return results

def main():
    """Run comprehensive tests"""
    print("="*70)
    print("QUADRANTDB MCP Tools - COMPREHENSIVE Test Suite")
    print("="*70)
    print("\nTesting all 7 tools with ALL parameter combinations:")
    print("  1. add_vector (content, metadata, pre-computed vector)")
    print("  2. get_vector (with/without vector)")
    print("  3. update_vector (content only, metadata only, both)")
    print("  4. search_similar (basic, with filter, custom top_k)")
    print("  5. search_by_metadata (basic, pagination, custom limit)")
    print("  6. index_repository (docs only, docs+code, custom patterns)")
    print("  7. delete_vector (soft delete, hard delete)")
    
    all_results = {}
    vector_id = None
    
    # Test 1: add_vector (all variants)
    vector_id, add_results = test_add_vector_all_variants()
    all_results["add_vector"] = all(add_results.values())
    
    # Test 2: get_vector (all variants)
    get_results = test_get_vector_all_variants(vector_id)
    all_results["get_vector"] = all(get_results.values()) if get_results else False
    
    # Test 3: update_vector (all variants)
    update_results = test_update_vector_all_variants(vector_id)
    all_results["update_vector"] = all(update_results.values()) if update_results else False
    
    # Test 4: search_similar (all variants)
    search_results = test_search_similar_all_variants()
    all_results["search_similar"] = all(search_results.values())
    
    # Test 5: search_by_metadata (all variants)
    metadata_results = test_search_by_metadata_all_variants()
    all_results["search_by_metadata"] = all(metadata_results.values())
    
    # Test 6: index_repository (all variants)
    index_results = test_index_repository_all_variants()
    all_results["index_repository"] = all(index_results.values())
    
    # Test 7: delete_vector (all variants)
    delete_results = test_delete_vector_all_variants(vector_id)
    all_results["delete_vector"] = all(delete_results.values()) if delete_results else False
    
    # Summary
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)
    
    for tool_name, result in all_results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {tool_name}")
    
    print(f"\n[PASS] Passed: {passed}/{total}")
    print(f"[FAIL] Failed: {total - passed}/{total}")
    print(f"[INFO] Success Rate: {passed / total * 100:.1f}%")
    print("="*70 + "\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

