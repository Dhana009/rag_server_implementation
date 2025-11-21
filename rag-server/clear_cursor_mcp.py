#!/usr/bin/env python3
"""
Clear Cursor MCP cache and configuration.

On Windows, Cursor stores MCP config in:
- %USERPROFILE%/.cursor/mcp.json
- Or %APPDATA%/Cursor/User/settings.json
"""

import os
import json
from pathlib import Path

def find_cursor_mcp_files():
    """Find all possible Cursor MCP configuration files"""
    files = []
    
    # Option 1: ~/.cursor/mcp.json (mentioned in README)
    user_home = Path.home()
    mcp_json = user_home / ".cursor" / "mcp.json"
    if mcp_json.exists():
        files.append(mcp_json)
    
    # Option 2: %APPDATA%\Cursor\User\settings.json
    appdata = os.getenv('APPDATA')
    if appdata:
        settings_json = Path(appdata) / "Cursor" / "User" / "settings.json"
        if settings_json.exists():
            files.append(settings_json)
    
    # Option 3: %APPDATA%\Cursor\User\globalStorage (for MCP cache)
    if appdata:
        global_storage = Path(appdata) / "Cursor" / "User" / "globalStorage"
        if global_storage.exists():
            # Look for MCP-related cache directories
            for item in global_storage.iterdir():
                if "mcp" in item.name.lower() or "claude" in item.name.lower():
                    files.append(item)
    
    return files

def clear_mcp_config():
    """Clear MCP configuration from Cursor"""
    print("="*70)
    print("Cursor MCP Cache Cleanup")
    print("="*70)
    
    files = find_cursor_mcp_files()
    
    if not files:
        print("\n[INFO] No Cursor MCP configuration files found.")
        print("\nCursor MCP config might be stored in:")
        print(f"  - {Path.home() / '.cursor' / 'mcp.json'}")
        print(f"  - {Path(os.getenv('APPDATA', '')) / 'Cursor' / 'User' / 'settings.json'}")
        return
    
    print(f"\n[INFO] Found {len(files)} potential MCP configuration file(s):\n")
    
    for file_path in files:
        print(f"  - {file_path}")
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'mcp' in content.lower() or 'rag-server' in content.lower():
                        print(f"    [CONTAINS MCP CONFIG]")
            except:
                pass
    
    print("\n" + "="*70)
    print("MANUAL CLEANUP INSTRUCTIONS")
    print("="*70)
    print("\nTo clear MCP cache in Cursor:")
    print("\nMETHOD 1: Via Settings UI")
    print("  1. Press Ctrl+, to open Settings")
    print("  2. Search for 'MCP' or 'Model Context Protocol'")
    print("  3. Find 'rag-server' or 'user-rag-server'")
    print("  4. Click the trash icon to remove it")
    print("  5. Restart Cursor")
    
    print("\nMETHOD 2: Edit mcp.json directly")
    if files:
        mcp_json = next((f for f in files if f.name == "mcp.json"), None)
        if mcp_json:
            print(f"  1. Open: {mcp_json}")
            print("  2. Remove the 'rag-server' entry from mcpServers")
            print("  3. Save and restart Cursor")
    
    print("\nMETHOD 3: Edit settings.json")
    settings_json = next((f for f in files if f.name == "settings.json"), None)
    if settings_json:
        print(f"  1. Press Ctrl+Shift+P")
        print("  2. Type 'Preferences: Open User Settings (JSON)'")
        print("  3. Find the 'mcp' section")
        print("  4. Remove the 'rag-server' or 'user-rag-server' entry")
        print("  5. Save and restart Cursor")
    
    print("\n" + "="*70)
    print("AUTOMATED CLEANUP (Backup First!)")
    print("="*70)
    print("\nTo automatically remove rag-server from config files:")
    print("  Run: python clear_cursor_mcp.py --remove")
    print("\nThis will:")
    print("  1. Backup the original files")
    print("  2. Remove rag-server/user-rag-server entries")
    print("  3. Save the cleaned configuration")
    print("="*70)

def remove_rag_server_from_config():
    """Automatically remove rag-server from MCP config files"""
    import shutil
    from datetime import datetime
    
    files = find_cursor_mcp_files()
    removed = False
    
    for file_path in files:
        if not file_path.is_file():
            continue
        
        try:
            # Backup
            backup_path = file_path.with_suffix(f".json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(file_path, backup_path)
            print(f"[OK] Backed up: {backup_path}")
            
            # Read and modify
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            modified = False
            
            # Check mcp.json format
            if 'mcpServers' in config:
                if 'rag-server' in config['mcpServers']:
                    del config['mcpServers']['rag-server']
                    modified = True
                    print(f"[OK] Removed 'rag-server' from {file_path.name}")
                if 'user-rag-server' in config['mcpServers']:
                    del config['mcpServers']['user-rag-server']
                    modified = True
                    print(f"[OK] Removed 'user-rag-server' from {file_path.name}")
            
            # Check settings.json format (mcp.servers)
            if 'mcp' in config and 'servers' in config['mcp']:
                if 'rag-server' in config['mcp']['servers']:
                    del config['mcp']['servers']['rag-server']
                    modified = True
                    print(f"[OK] Removed 'rag-server' from {file_path.name}")
                if 'user-rag-server' in config['mcp']['servers']:
                    del config['mcp']['servers']['user-rag-server']
                    modified = True
                    print(f"[OK] Removed 'user-rag-server' from {file_path.name}")
            
            if modified:
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                removed = True
                print(f"[OK] Updated: {file_path}")
            else:
                # Remove backup if no changes
                backup_path.unlink()
                print(f"[INFO] No rag-server config found in {file_path.name}")
        
        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {e}")
    
    if removed:
        print("\n[OK] MCP configuration cleaned!")
        print("Please restart Cursor for changes to take effect.")
    else:
        print("\n[INFO] No rag-server configuration found to remove.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        print("="*70)
        print("Removing rag-server from MCP configuration...")
        print("="*70)
        remove_rag_server_from_config()
    else:
        clear_mcp_config()

