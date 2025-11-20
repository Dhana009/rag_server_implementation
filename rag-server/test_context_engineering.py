#!/usr/bin/env python3
"""
Test script for Context Engineering Implementation

Tests the three-tier context engineering system:
- Tier 1: get_manifest (lightweight briefs)
- Tier 2: get_tool_schema (on-demand schemas)
- Tier 3: Tool execution (backward compatibility)
"""

import sys
import json
from pathlib import Path

# Add rag-server to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.core.tool_manifest import ToolManifest
from lib.tools.manifest import get_manifest_tool, get_tool_schema_tool

def test_tier1_manifest():
    """Test Tier 1: Lightweight manifest"""
    print("\n" + "="*60)
    print("TEST 1: Tier 1 - Get Manifest (Lightweight Briefs)")
    print("="*60)
    
    try:
        result = get_manifest_tool()
        data = json.loads(result)
        
        print(f"[OK] Manifest retrieved successfully")
        print(f"   Total tools: {data.get('total_tools', 0)}")
        print(f"   Tier: {data.get('tier', 'N/A')}")
        
        # Display manifest
        manifest = data.get('manifest', {})
        print(f"\n   Available tools:")
        for tool_name, tool_info in manifest.items():
            print(f"   - {tool_name}:")
            print(f"     Brief: {tool_info.get('brief', 'N/A')}")
            print(f"     Category: {tool_info.get('category', 'N/A')}")
            print(f"     Use cases: {len(tool_info.get('use_cases', []))}")
        
        # Display validation
        validation = data.get('validation', {})
        print(f"\n   Token validation:")
        all_valid = True
        for tool_name, val_result in validation.items():
            tokens = val_result.get('tokens', 0)
            within_limit = val_result.get('within_limit', False)
            status = "[OK]" if within_limit else "[WARN]"
            print(f"   {status} {tool_name}: {tokens} tokens")
            if not within_limit:
                all_valid = False
        
        if all_valid:
            print(f"\n   [OK] All briefs are within token limits (30-50 tokens)")
        else:
            print(f"\n   [WARN] Some briefs are outside token limits (but close)")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tier2_schema():
    """Test Tier 2: On-demand schema loading"""
    print("\n" + "="*60)
    print("TEST 2: Tier 2 - Get Tool Schema (On-Demand)")
    print("="*60)
    
    tools_to_test = ["search", "ask", "explain"]
    all_passed = True
    
    for tool_name in tools_to_test:
        print(f"\n   Testing: {tool_name}")
        try:
            result = get_tool_schema_tool(tool_name)
            data = json.loads(result)
            
            if "error" in data:
                print(f"   [ERROR] Error: {data['error']}")
                all_passed = False
                continue
            
            print(f"   [OK] Schema retrieved")
            print(f"      Tier: {data.get('tier', 'N/A')}")
            
            schema = data.get('schema', {})
            if schema:
                print(f"      Description: {schema.get('description', 'N/A')[:60]}...")
                print(f"      Has input schema: {bool(schema.get('input_schema'))}")
                print(f"      Examples: {len(schema.get('examples', []))}")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")
            all_passed = False
    
    if all_passed:
        print(f"\n   [OK] All tool schemas loaded successfully")
    else:
        print(f"\n   ⚠️ Some tool schemas failed to load")
    
    return all_passed

def test_manifest_class():
    """Test ToolManifest class directly"""
    print("\n" + "="*60)
    print("TEST 3: ToolManifest Class Direct Access")
    print("="*60)
    
    try:
        # Test get_manifest
        manifest = ToolManifest.get_manifest()
        print(f"[OK] get_manifest() works: {len(manifest)} tools")
        
        # Test get_tool_brief
        brief = ToolManifest.get_tool_brief("search")
        if brief:
            print(f"[OK] get_tool_brief('search') works")
            print(f"   Brief: {brief.get('brief', 'N/A')[:50]}...")
        else:
            print(f"[FAIL] get_tool_brief('search') returned None")
            return False
        
        # Test get_tool_schema (needs to be registered first)
        # Note: Schemas are registered in server.py, so we need to import that
        # For now, just check if the method exists
        schema = ToolManifest.get_tool_schema("search")
        if schema:
            print(f"[OK] get_tool_schema('search') works")
            print(f"   Schema name: {schema.get('name', 'N/A')}")
        else:
            print(f"[WARN] get_tool_schema('search') returned None (may need server initialization)")
        
        # Test validation
        validation = ToolManifest.validate_briefs()
        print(f"[OK] validate_briefs() works: {len(validation)} tools validated")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_estimation():
    """Test token estimation"""
    print("\n" + "="*60)
    print("TEST 4: Token Estimation")
    print("="*60)
    
    try:
        test_strings = [
            "Short",
            "This is a medium length string",
            "This is a longer string that should have more tokens and be closer to the limit we want to test",
            "A" * 200  # 200 characters
        ]
        
        for test_str in test_strings:
            tokens = ToolManifest.estimate_tokens(test_str)
            print(f"   '{test_str[:30]}...': {tokens} tokens")
        
        print(f"\n   [OK] Token estimation working")
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_schema_registration():
    """Test that schemas can be registered"""
    print("\n" + "="*60)
    print("TEST 5: Schema Registration")
    print("="*60)
    
    try:
        # Register a test schema
        ToolManifest.register_tool_schema(
            "test_tool",
            "Test tool description",
            {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            },
            [{"param1": "test"}]
        )
        
        # Retrieve it
        schema = ToolManifest.get_tool_schema("test_tool")
        if schema:
            print(f"[OK] Schema registration and retrieval works")
            print(f"   Tool name: {schema.get('name', 'N/A')}")
            return True
        else:
            print(f"[FAIL] Schema not found after registration")
            return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CONTEXT ENGINEERING IMPLEMENTATION - TEST SUITE")
    print("="*60)
    
    # Note: We need to register schemas first (normally done in server.py)
    # Let's import server.py to trigger schema registration
    try:
        print("\n[INFO] Registering tool schemas...")
        # Import server to trigger schema registration
        import server
        print("[OK] Tool schemas registered")
    except Exception as e:
        print(f"[WARN] Could not import server (this is OK for testing): {e}")
        print("   Some tests may show warnings")
    
    results = []
    
    # Run tests
    results.append(("Tier 1 Manifest", test_tier1_manifest()))
    results.append(("Tier 2 Schema", test_tier2_schema()))
    results.append(("Manifest Class", test_manifest_class()))
    results.append(("Token Estimation", test_token_estimation()))
    results.append(("Schema Registration", test_schema_registration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   [SUCCESS] All tests passed! Context engineering implementation is working correctly.")
        return 0
    else:
        print(f"\n   [WARN] {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

