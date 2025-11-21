#!/usr/bin/env python3
"""
Index data from an external repository into Qdrant.

Usage:
    # From external repo directory
    python index_external_repo.py --repo-path "D:/my-other-project"
    
    # Or set environment variables
    $env:MCP_PROJECT_ROOT="D:/my-other-project"
    python index_external_repo.py
"""

import sys
import os
import argparse
from pathlib import Path

# Add rag-server to path
rag_server_dir = Path(__file__).parent
sys.path.insert(0, str(rag_server_dir))

from lib.indexing.index_all import main as index_main


def main():
    parser = argparse.ArgumentParser(
        description="Index external repository into Qdrant"
    )
    parser.add_argument(
        "--repo-path",
        help="Path to external repository to index (absolute or relative)"
    )
    parser.add_argument(
        "--config-file",
        help="Path to mcp-config.json (if not in external repo)"
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Index documentation only"
    )
    parser.add_argument(
        "--code-only",
        action="store_true",
        help="Index code only"
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Cloud collection only"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Local collection only"
    )
    
    args = parser.parse_args()
    
    # Set project root if provided
    if args.repo_path:
        repo_path = Path(args.repo_path).resolve()
        if not repo_path.exists():
            print(f"Error: Repository path does not exist: {repo_path}")
            return 1
        
        os.environ["MCP_PROJECT_ROOT"] = str(repo_path)
        print(f"Setting project root to: {repo_path}")
    
    # Set config file if provided
    if args.config_file:
        config_path = Path(args.config_file).resolve()
        if not config_path.exists():
            print(f"Error: Config file does not exist: {config_path}")
            return 1
        
        os.environ["MCP_CONFIG_FILE"] = str(config_path)
        print(f"Using config file: {config_path}")
    
    # Ensure .env file is set (point to rag-server's .env)
    if not os.getenv("MCP_ENV_FILE"):
        env_file = rag_server_dir / ".env.qdrant"
        if env_file.exists():
            os.environ["MCP_ENV_FILE"] = str(env_file)
            print(f"Using .env file: {env_file}")
        else:
            print(f"Warning: .env file not found at {env_file}")
            print("Set MCP_ENV_FILE environment variable to point to your .env file")
    
    # Convert args to index_all format
    sys.argv = ['index_external_repo.py']
    if args.docs_only:
        sys.argv.append('--docs-only')
    if args.code_only:
        sys.argv.append('--code-only')
    if args.cloud:
        sys.argv.append('--cloud')
    if args.local:
        sys.argv.append('--local')
    
    # Run indexing
    return index_main()


if __name__ == "__main__":
    sys.exit(main())

