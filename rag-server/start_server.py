#!/usr/bin/env python3
"""Start MCP server for testing"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from server import main
import asyncio

if __name__ == "__main__":
    server_name = os.getenv("MCP_SERVER_NAME", "rag-server")
    print(f"Starting MCP Server ({server_name})...")
    print("Press Ctrl+C to stop")
    print()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")

