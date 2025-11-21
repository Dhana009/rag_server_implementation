#!/usr/bin/env python3
"""
Verify MCP server configuration is correct.
"""

import json
from pathlib import Path

config = {
    "rag-server": {
        "command": "C:\\Python313\\python.exe",
        "args": [
            "D:\\planning\\rag_server_implementation\\rag-server\\server.py"
        ],
        "cwd": "D:\\planning\\rag_server_implementation\\rag-server",
        "env": {
            "MCP_ENV_FILE": "D:\\planning\\rag_server_implementation\\rag-server\\.env.qdrant"
        }
    }
}

print("="*70)
print("MCP Configuration Verification")
print("="*70)

# Check Python path
python_path = Path(config["rag-server"]["command"])
if python_path.exists():
    print(f"[OK] Python executable exists: {python_path}")
else:
    print(f"[ERROR] Python executable not found: {python_path}")

# Check server.py path
server_path = Path(config["rag-server"]["args"][0])
if server_path.exists():
    print(f"[OK] Server script exists: {server_path}")
else:
    print(f"[ERROR] Server script not found: {server_path}")

# Check working directory
cwd = Path(config["rag-server"]["cwd"])
if cwd.exists() and cwd.is_dir():
    print(f"[OK] Working directory exists: {cwd}")
else:
    print(f"[ERROR] Working directory not found: {cwd}")

# Check env file
env_file = Path(config["rag-server"]["env"]["MCP_ENV_FILE"])
if env_file.exists():
    print(f"[OK] Environment file exists: {env_file}")
    # Check if it has required variables
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            has_url = "QDRANT_CLOUD_URL" in content
            has_key = "QDRANT_API_KEY" in content
            if has_url and has_key:
                print(f"[OK] Environment file contains required variables")
            else:
                missing = []
                if not has_url:
                    missing.append("QDRANT_CLOUD_URL")
                if not has_key:
                    missing.append("QDRANT_API_KEY")
                print(f"[WARN] Missing variables in env file: {', '.join(missing)}")
    except Exception as e:
        print(f"[WARN] Could not read env file: {e}")
else:
    print(f"[ERROR] Environment file not found: {env_file}")

print("\n" + "="*70)
print("Configuration Summary")
print("="*70)
print("\nYour configuration:")
print(json.dumps(config, indent=2))
print("\n[OK] Configuration looks correct!")
print("\nMake sure:")
print("  1. The .env.qdrant file contains QDRANT_CLOUD_URL and QDRANT_API_KEY")
print("  2. Restart Cursor after adding this configuration")
print("  3. Check MCP server status in Cursor to verify connection")
print("="*70)

