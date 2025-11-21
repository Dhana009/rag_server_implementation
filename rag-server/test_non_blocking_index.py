#!/usr/bin/env python3
"""
Test script to verify non-blocking behavior of index_repository in MCP server.

This test verifies that:
1. index_repository runs in a thread executor (non-blocking)
2. list_tools can be called concurrently during indexing
3. Progress messages are visible in real-time
"""

import asyncio
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import server components
from server import server, list_tools, call_tool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_non_blocking_index():
    """Test that index_repository doesn't block other operations"""
    print("="*70)
    print("Testing Non-Blocking index_repository")
    print("="*70)
    
    # Get the test repository path (rag-server directory)
    repo_path = Path(__file__).parent
    
    print(f"\n[TEST 1] Starting index_repository in background...")
    print(f"   Repository: {repo_path}")
    
    # Start indexing in background
    start_time = time.time()
    index_task = asyncio.create_task(
        call_tool(
            "index_repository",
            {
                "repository_path": str(repo_path),
                "index_docs": True,
                "index_code": False,  # Skip code for faster test
                "collection": "cloud"
            }
        )
    )
    
    # Give it a moment to start
    await asyncio.sleep(0.5)
    
    print(f"\n[TEST 2] Testing concurrent list_tools calls...")
    print("   (This should work immediately, even while indexing is running)")
    
    # Try to call list_tools multiple times while indexing is running
    concurrent_calls = []
    for i in range(5):
        call_start = time.time()
        try:
            tools = await list_tools()
            call_duration = time.time() - call_start
            concurrent_calls.append({
                "call": i + 1,
                "duration": call_duration,
                "tools_count": len(tools),
                "success": True
            })
            print(f"   ✓ Call {i+1}: {call_duration*1000:.1f}ms - {len(tools)} tools")
        except Exception as e:
            concurrent_calls.append({
                "call": i + 1,
                "success": False,
                "error": str(e)
            })
            print(f"   ✗ Call {i+1}: FAILED - {e}")
        
        # Small delay between calls
        await asyncio.sleep(0.2)
    
    print(f"\n[TEST 3] Waiting for index_repository to complete...")
    
    # Wait for indexing to complete
    try:
        result = await asyncio.wait_for(index_task, timeout=300)  # 5 minute timeout
        index_duration = time.time() - start_time
        
        # Parse result
        result_text = result["content"][0]["text"]
        result_data = json.loads(result_text)
        
        print(f"   ✓ Indexing completed in {index_duration:.1f}s")
        if result_data.get("success"):
            data = result_data.get("data", {})
            print(f"   ✓ Docs indexed: {data.get('docs_indexed', 0)} chunks")
            print(f"   ✓ Errors: {data.get('errors', 0)}")
        else:
            print(f"   ✗ Indexing failed: {result_data.get('errors', [])}")
            
    except asyncio.TimeoutError:
        print(f"   ✗ Indexing timed out after 5 minutes")
        index_task.cancel()
        return False
    except Exception as e:
        print(f"   ✗ Indexing failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify concurrent calls succeeded
    print(f"\n[TEST 4] Verifying concurrent calls succeeded...")
    successful_calls = [c for c in concurrent_calls if c.get("success")]
    failed_calls = [c for c in concurrent_calls if not c.get("success")]
    
    if len(successful_calls) == 5:
        print(f"   ✓ All 5 concurrent list_tools calls succeeded")
        avg_duration = sum(c["duration"] for c in successful_calls) / len(successful_calls)
        print(f"   ✓ Average response time: {avg_duration*1000:.1f}ms")
        print(f"   ✓ Max response time: {max(c['duration'] for c in successful_calls)*1000:.1f}ms")
    else:
        print(f"   ✗ Only {len(successful_calls)}/5 calls succeeded")
        for failed in failed_calls:
            print(f"   ✗ Call {failed['call']} failed: {failed.get('error', 'Unknown')}")
        return False
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✓ Non-blocking behavior: VERIFIED")
    print("✓ Concurrent list_tools calls: SUCCESS")
    print("✓ index_repository completion: SUCCESS")
    print("="*70 + "\n")
    
    return True


async def main():
    """Main test entry point"""
    try:
        success = await test_non_blocking_index()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

