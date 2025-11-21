#!/usr/bin/env python3
"""Quick test with progress indicators"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ["MCP_ENV_FILE"] = str(Path(__file__).parent / ".env.qdrant")

from lib.tools.vector_crud import (
    add_vector, get_vector, update_vector, delete_vector,
    search_similar, search_by_metadata
)

def print_progress(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

print("="*70)
print("QUICK TEST SUITE - With Progress Indicators")
print("="*70)

results = {}
vector_id = None

# Test 1: add_vector
print_progress("TEST 1: add_vector...")
try:
    result = add_vector(
        content="Quick test content",
        metadata={"category": "test", "type": "quick_test"}
    )
    data = json.loads(result)
    if data["success"]:
        vector_id = data["data"]["vector_id"]
        results["add_vector"] = True
        print_progress(f"  PASS: Vector ID = {vector_id}")
    else:
        results["add_vector"] = False
        print_progress(f"  FAIL: {data.get('errors', [])}")
except Exception as e:
    results["add_vector"] = False
    print_progress(f"  ERROR: {e}")

# Test 2: get_vector
print_progress("TEST 2: get_vector...")
try:
    if vector_id:
        result = get_vector(vector_id, include_vector=False)
        data = json.loads(result)
        results["get_vector"] = data["success"]
        print_progress(f"  {'PASS' if data['success'] else 'FAIL'}")
    else:
        results["get_vector"] = False
        print_progress("  SKIP: No vector_id")
except Exception as e:
    results["get_vector"] = False
    print_progress(f"  ERROR: {e}")

# Test 3: update_vector
print_progress("TEST 3: update_vector...")
try:
    if vector_id:
        result = update_vector(
            vector_id=vector_id,
            metadata={"updated": True}
        )
        data = json.loads(result)
        results["update_vector"] = data["success"]
        print_progress(f"  {'PASS' if data['success'] else 'FAIL'}")
    else:
        results["update_vector"] = False
        print_progress("  SKIP: No vector_id")
except Exception as e:
    results["update_vector"] = False
    print_progress(f"  ERROR: {e}")

# Test 4: search_similar
print_progress("TEST 4: search_similar...")
try:
    result = search_similar(query="test", top_k=5)
    data = json.loads(result)
    results["search_similar"] = data["success"]
    count = data.get("data", {}).get("count", 0)
    print_progress(f"  {'PASS' if data['success'] else 'FAIL'}: Found {count} results")
except Exception as e:
    results["search_similar"] = False
    print_progress(f"  ERROR: {e}")

# Test 5: search_by_metadata
print_progress("TEST 5: search_by_metadata...")
try:
    result = search_by_metadata(
        filter={"must": [{"key": "category", "match": "test"}]},
        limit=10
    )
    data = json.loads(result)
    results["search_by_metadata"] = data["success"]
    count = data.get("data", {}).get("count", 0)
    print_progress(f"  {'PASS' if data['success'] else 'FAIL'}: Found {count} results")
except Exception as e:
    results["search_by_metadata"] = False
    print_progress(f"  ERROR: {e}")

# Test 6: delete_vector (soft)
print_progress("TEST 6: delete_vector (soft)...")
try:
    if vector_id:
        result = delete_vector(vector_id, soft_delete=True)
        data = json.loads(result)
        results["delete_vector"] = data["success"]
        print_progress(f"  {'PASS' if data['success'] else 'FAIL'}")
    else:
        results["delete_vector"] = False
        print_progress("  SKIP: No vector_id")
except Exception as e:
    results["delete_vector"] = False
    print_progress(f"  ERROR: {e}")

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
passed = sum(1 for v in results.values() if v)
total = len(results)
for test_name, result in results.items():
    status = "[PASS]" if result else "[FAIL]"
    print(f"  {status}: {test_name}")
print(f"\n[PASS] Passed: {passed}/{total}")
print(f"[FAIL] Failed: {total - passed}/{total}")
print("="*70)

sys.exit(0 if passed == total else 1)

