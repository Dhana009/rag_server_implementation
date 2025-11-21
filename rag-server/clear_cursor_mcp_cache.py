#!/usr/bin/env python3
"""
Find and clear Cursor MCP cache and configuration.

On Windows, Cursor stores MCP settings in:
- %APPDATA%\Cursor\User\settings.json
- Or in MCP-specific configuration files
"""

import os
import json
import shutil
from pathlib import Path

def find_cursor_settings():
    """Find Cursor settings directory"""
    appdata = os.getenv('APPDATA')
    if not appdata:
        print("[ERROR] APPDATA environment variable not found")
        return None
    
    cursor_settings = Path(appdata) / "Cursor" / "User"
    
    if not cursor_settings.exists():
        print(f"[WARN] Cursor settings directory not found at: {cursor_settings}")
        return None
    
    return cursor_settings

def find_mcp_config_in_settings(settings_dir):
    """Find MCP configuration in settings.json"""
    settings_file = settings_dir / "settings.json"
    
    if not settings_file.exists():
        print(f"[INFO] settings.json not found at: {settings_file}")
        return None, None
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Check for MCP configuration
        mcp_config = settings.get("mcp", {})
        if mcp_config:
            return settings_file, settings
        else:
            print("[INFO] No MCP configuration found in settings.json")
            return settings_file, settings
    
    except Exception as e:
        print(f"[ERROR] Failed to read settings.json: {e}")
        return None, None

def clear_mcp_cache():
    """Clear MCP cache and configuration"""
    print("="*70)
    print("Cursor MCP Cache Cleanup")
    print("="*70)
    
    # Find Cursor settings
    settings_dir = find_cursor_settings()
    if not settings_dir:
        print("\n[INFO] Could not find Cursor settings directory.")
        print("Please manually clear MCP cache in Cursor settings.")
        return
    
    print(f"\n[OK] Found Cursor settings at: {settings_dir}")
    
    # Find MCP config
    settings_file, settings = find_mcp_config_in_settings(settings_dir)
    
    if not settings_file:
        print("\n[INFO] No settings.json found. Cache may already be clear.")
        return
    
    # Check for MCP servers
    mcp_servers = settings.get("mcp", {}).get("servers", {})
    
    if not mcp_servers:
        print("\n[INFO] No MCP servers found in settings. Cache is already clear.")
        return
    
    print(f"\n[INFO] Found {len(mcp_servers)} MCP server(s) in configuration:")
    for server_name in mcp_servers.keys():
        print(f"  - {server_name}")
    
    # Look for rag-server specifically
    rag_server_config = mcp_servers.get("rag-server") or mcp_servers.get("user-rag-server")
    
    if rag_server_config:
        print(f"\n[INFO] Found rag-server configuration")
        print(f"  Command: {rag_server_config.get('command', 'N/A')}")
        print(f"  Args: {rag_server_config.get('args', 'N/A')}")
    
    print("\n" + "="*70)
    print("MANUAL CLEANUP REQUIRED")
    print("="*70)
    print("\nTo clear MCP cache in Cursor:")
    print("\n1. Open Cursor Settings:")
    print("   - Press Ctrl+, (or File -> Preferences -> Settings)")
    print("   - Or open settings.json directly:")
    print(f"     {settings_file}")
    print("\n2. Search for 'mcp' in the settings")
    print("\n3. Find the 'rag-server' or 'user-rag-server' entry")
    print("\n4. Remove the entire server configuration")
    print("\n5. Save and restart Cursor")
    print("\n" + "="*70)
    print("ALTERNATIVE: Clear via Command Palette")
    print("="*70)
    print("\n1. Press Ctrl+Shift+P")
    print("2. Type 'Preferences: Open User Settings (JSON)'")
    print("3. Find and remove the MCP server entry")
    print("4. Save and restart Cursor")
    print("\n" + "="*70)
    print("SETTINGS FILE LOCATION")
    print("="*70)
    print(f"\n{settings_file}")
    print("\nYou can edit this file directly to remove MCP configuration.")
    print("="*70)

if __name__ == "__main__":
    clear_mcp_cache()

