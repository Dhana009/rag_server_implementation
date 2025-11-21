#!/usr/bin/env python3
"""
Test script for QUADRANTDB tools - Verify all 6 tools work correctly.

Tests:
1. add_vector - Store new data
2. get_vector - Retrieve by ID
3. update_vector - Update content/metadata
4. delete_vector - Delete (soft and hard)
5. search_similar - Semantic search
6. search_by_metadata - Metadata filtering
"""

import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import server to register schemas
import server

from lib.tools.vector_crud import (
    add_vector, get_vector, update_vector, delete_vector,
    search_similar, search_by_metadata
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_add_vector():
    """Test add_vector tool"""
    print("\n" + "="*60)
    print("[TEST 1] Testing add_vector...")
    print("="*60)
    
    try:
        # Test 1: Add with content
        result = add_vector(
            content="This is a test vector for QA automation",
            metadata={"category": "test", "type": "qa", "file_path": "test_qa.py"}
        )
        data = json.loads(result)
        
        if data["success"]:
            vector_id = data["data"]["vector_id"]
            print(f"✅ add_vector with content: SUCCESS")
            print(f"   Vector ID: {vector_id}")
            return vector_id
        else:
            print(f"❌ add_vector with content: FAILED")
            print(f"   Error: {data['errors']}")
            return None
            
    except Exception as e:
        print(f"❌ add_vector test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_vector(vector_id):
    """Test get_vector tool"""
    print("\n" + "="*60)
    print("[TEST 2] Testing get_vector...")
    print("="*60)
    
    if not vector_id:
        print("⚠️  Skipping get_vector test (no vector_id)")
        return False
    
    try:
        # Test 1: Get without vector
        result = get_vector(vector_id, include_vector=False)
        data = json.loads(result)
        
        if data["success"]:
            print(f"✅ get_vector (without vector): SUCCESS")
            print(f"   Vector ID: {data['data']['vector_id']}")
            print(f"   Metadata: {data['data']['metadata']}")
            return True
        else:
            print(f"❌ get_vector: FAILED")
            print(f"   Error: {data['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ get_vector test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_vector(vector_id):
    """Test update_vector tool"""
    print("\n" + "="*60)
    print("[TEST 3] Testing update_vector...")
    print("="*60)
    
    if not vector_id:
        print("⚠️  Skipping update_vector test (no vector_id)")
        return False
    
    try:
        # Test: Update metadata
        result = update_vector(
            vector_id=vector_id,
            metadata={"category": "test", "type": "qa", "updated": True, "status": "verified"}
        )
        data = json.loads(result)
        
        if data["success"]:
            print(f"✅ update_vector: SUCCESS")
            print(f"   Updated metadata: {data['data']['metadata']}")
            return True
        else:
            print(f"❌ update_vector: FAILED")
            print(f"   Error: {data['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ update_vector test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_similar():
    """Test search_similar tool"""
    print("\n" + "="*60)
    print("[TEST 4] Testing search_similar...")
    print("="*60)
    
    try:
        # Test: Semantic search
        result = search_similar(
            query="QA automation test",
            top_k=5
        )
        data = json.loads(result)
        
        if data["success"]:
            count = data["data"]["count"]
            print(f"✅ search_similar: SUCCESS")
            print(f"   Found {count} results")
            if count > 0:
                print(f"   Top result ID: {data['data']['results'][0]['vector_id']}")
                print(f"   Top result score: {data['data']['results'][0]['score']:.4f}")
            return True
        else:
            print(f"❌ search_similar: FAILED")
            print(f"   Error: {data['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ search_similar test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_by_metadata():
    """Test search_by_metadata tool"""
    print("\n" + "="*60)
    print("[TEST 5] Testing search_by_metadata...")
    print("="*60)
    
    try:
        # Test: Filter by category
        result = search_by_metadata(
            filter={"must": [{"key": "category", "match": "test"}]},
            limit=10
        )
        data = json.loads(result)
        
        if data["success"]:
            count = data["data"]["count"]
            print(f"✅ search_by_metadata: SUCCESS")
            print(f"   Found {count} results with category='test'")
            return True
        else:
            print(f"❌ search_by_metadata: FAILED")
            print(f"   Error: {data['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ search_by_metadata test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_delete_vector(vector_id, soft_delete=True):
    """Test delete_vector tool"""
    print("\n" + "="*60)
    print(f"[TEST 6] Testing delete_vector (soft_delete={soft_delete})...")
    print("="*60)
    
    if not vector_id:
        print("⚠️  Skipping delete_vector test (no vector_id)")
        return False
    
    try:
        # Test: Soft delete
        result = delete_vector(vector_id, soft_delete=soft_delete)
        data = json.loads(result)
        
        if data["success"]:
            print(f"✅ delete_vector (soft_delete={soft_delete}): SUCCESS")
            print(f"   Deleted vector ID: {data['data']['vector_id']}")
            return True
        else:
            print(f"❌ delete_vector: FAILED")
            print(f"   Error: {data['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ delete_vector test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all QUADRANTDB tool tests"""
    print("="*60)
    print("QUADRANTDB Tools Test Suite")
    print("="*60)
    
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
    
    # Test 6: delete_vector (soft delete)
    results["delete_vector_soft"] = test_delete_vector(vector_id, soft_delete=True)
    
    # Test 7: delete_vector (hard delete) - use a new vector
    vector_id2 = test_add_vector()
    results["delete_vector_hard"] = test_delete_vector(vector_id2, soft_delete=False) if vector_id2 else False
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {passed / total * 100:.1f}%")
    print("="*60 + "\n")
    
    return passed == total


def main():
    """Main entry point"""
    try:
        success = run_all_tests()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

