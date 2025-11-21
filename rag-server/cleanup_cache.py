#!/usr/bin/env python3
"""
Clean up cache files and prepare for MCP server testing.

Removes:
- Python __pycache__ directories
- .pyc files
- Log files (optional)
"""

import os
import shutil
from pathlib import Path

def cleanup_cache():
    """Clean up cache files"""
    rag_server_dir = Path(__file__).parent
    
    print("="*60)
    print("Cleaning up cache files...")
    print("="*60)
    
    # Remove __pycache__ directories
    print("\n[1] Removing __pycache__ directories...")
    pycache_dirs = list(rag_server_dir.rglob("__pycache__"))
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            print(f"  [OK] Removed: {pycache_dir.relative_to(rag_server_dir)}")
        except Exception as e:
            print(f"  [WARN] Could not remove {pycache_dir}: {e}")
    
    # Remove .pyc files
    print("\n[2] Removing .pyc files...")
    pyc_files = list(rag_server_dir.rglob("*.pyc"))
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
            print(f"  [OK] Removed: {pyc_file.relative_to(rag_server_dir)}")
        except Exception as e:
            print(f"  [WARN] Could not remove {pyc_file}: {e}")
    
    # Optional: Clear log files
    print("\n[3] Log files (keeping for debugging)...")
    log_files = list(rag_server_dir.glob("*.log"))
    if log_files:
        print(f"  Found {len(log_files)} log file(s). Keeping them for debugging.")
        print("  To clear logs, delete: " + ", ".join([f.name for f in log_files]))
    
    print("\n" + "="*60)
    print("[OK] Cache cleanup complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. In Cursor: Open Settings (Ctrl+,)")
    print("2. Search for 'MCP' or 'Model Context Protocol'")
    print("3. Find your rag-server configuration")
    print("4. Remove it, then re-add it")
    print("5. Restart Cursor or reload the MCP server")
    print("\nMCP Server Path:")
    print(f"  {rag_server_dir / 'server.py'}")
    print("\nCommand to run:")
    print(f"  python \"{rag_server_dir / 'server.py'}\"")

if __name__ == "__main__":
    cleanup_cache()


