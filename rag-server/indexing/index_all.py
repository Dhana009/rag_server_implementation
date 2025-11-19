#!/usr/bin/env python3
"""
Backward compatibility wrapper for old index_all.py command.
Use 'mcp index' instead for better user experience.
"""
import sys
from pathlib import Path

# Redirect to actual implementation in lib/
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.indexing.index_all import main as index_main
import argparse

if __name__ == "__main__":
    # Parse old-style arguments and convert to new format
    parser = argparse.ArgumentParser(description="Index project documentation and code (legacy wrapper)")
    parser.add_argument("--docs-only", action="store_true", help="Index documentation only")
    parser.add_argument("--code-only", action="store_true", help="Index code only")
    parser.add_argument("--cloud", action="store_true", help="Cloud collection only")
    parser.add_argument("--local", action="store_true", help="Local collection only")
    parser.add_argument("--prune", action="store_true", help="Actually delete orphaned chunks (otherwise dry-run)")
    args = parser.parse_args()
    
    # Convert to new format
    class NewArgs:
        docs = args.docs_only
        code = args.code_only
        cloud = args.cloud
        local = args.local
        cleanup = args.prune
    
    # Call the actual implementation with old-style args
    sys.argv = ['index_all.py']
    if args.docs_only:
        sys.argv.append('--docs-only')
    if args.code_only:
        sys.argv.append('--code-only')
    if args.cloud:
        sys.argv.append('--cloud')
    if args.local:
        sys.argv.append('--local')
    if args.prune:
        sys.argv.append('--prune')
    
    sys.exit(index_main())
