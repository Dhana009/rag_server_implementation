#!/usr/bin/env python3
"""Check which Qdrant instance is configured"""

import os
from pathlib import Path
from dotenv import load_dotenv

rag_server_dir = Path(__file__).parent.resolve()

# Check for .env.qdrant first
env_qdrant_path = rag_server_dir / ".env.qdrant"
env_path = rag_server_dir / ".env"

print("="*60)
print("Qdrant Configuration Check")
print("="*60)

# Check which file exists
if env_qdrant_path.exists():
    print(f"\n[FOUND] .env.qdrant file exists")
    load_dotenv(env_qdrant_path)
    source_file = ".env.qdrant"
elif env_path.exists():
    print(f"\n[FOUND] .env file exists")
    load_dotenv(env_path)
    source_file = ".env"
else:
    print(f"\n[ERROR] No .env or .env.qdrant file found!")
    print(f"  Expected location: {rag_server_dir / '.env'}")
    exit(1)

# Get Qdrant configuration
qdrant_url = os.getenv("QDRANT_CLOUD_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_collection = os.getenv("QDRANT_COLLECTION", "mcp-rag")

print(f"\nConfiguration loaded from: {source_file}")
print(f"\nQdrant Configuration:")
print(f"  URL: {qdrant_url}")
print(f"  API Key: {qdrant_api_key[:20]}..." if qdrant_api_key else "  API Key: NOT SET")
print(f"  Collection: {qdrant_collection}")

# Determine if it's real Qdrant Cloud or local
if qdrant_url:
    if "cloud.qdrant.io" in qdrant_url or "qdrant.io" in qdrant_url:
        print(f"\n[STATUS] Using REAL Qdrant Cloud instance")
        print(f"  This is a production Qdrant Cloud cluster")
    elif "localhost" in qdrant_url or "127.0.0.1" in qdrant_url:
        print(f"\n[STATUS] Using LOCAL Qdrant instance")
        print(f"  This is a local Qdrant instance (not cloud)")
    else:
        print(f"\n[STATUS] Using custom Qdrant instance")
        print(f"  URL: {qdrant_url}")
else:
    print(f"\n[ERROR] QDRANT_CLOUD_URL not set!")

print("\n" + "="*60)

