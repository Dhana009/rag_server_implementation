#!/usr/bin/env python3
"""
MCP RAG Server - Unified CLI
User-friendly command-line interface for all MCP operations
"""
import argparse
import sys
from pathlib import Path

# Add rag-server to path
sys.path.insert(0, str(Path(__file__).parent))


def cmd_index(args):
    """Index command - index documentation and code"""
    from lib.indexing.index_all import main as index_main
    
    # Convert new args to old format
    sys.argv = ['index_all.py']
    if args.docs:
        sys.argv.append('--docs-only')
    if args.code:
        sys.argv.append('--code-only')
    if args.cloud:
        sys.argv.append('--cloud')
    if args.local:
        sys.argv.append('--local')
    if args.cleanup:
        sys.argv.append('--prune')
    
    return index_main()


def cmd_stats(args):
    """Stats command - show collection statistics"""
    from scripts.check_stats import main as stats_main
    
    sys.argv = ['check_stats.py']
    if args.cloud:
        sys.argv.append('--cloud')
    if args.local:
        sys.argv.append('--local')
    
    return stats_main()


def cmd_recover(args):
    """Recover command - recover soft-deleted chunks"""
    from scripts.recover_deleted import main as recover_main
    
    sys.argv = ['recover_deleted.py']
    if args.all:
        sys.argv.append('--recover')
    if args.file:
        sys.argv.extend(['--file', args.file])
    if args.cloud:
        sys.argv.append('--cloud')
    if args.local:
        sys.argv.append('--local')
    
    return recover_main()


def cmd_delete(args):
    """Delete command - permanently delete soft-deleted chunks"""
    from scripts.permanent_delete import main as delete_main
    
    sys.argv = ['permanent_delete.py']
    if args.preview:
        sys.argv.append('--preview')
    if args.confirm:
        sys.argv.append('--delete')
    if args.file:
        sys.argv.extend(['--file', args.file])
    if args.cloud:
        sys.argv.append('--cloud')
    if args.local:
        sys.argv.append('--local')
    if args.force:
        sys.argv.append('--force')
    
    return delete_main()


def cmd_start(args):
    """Start command - start the MCP server"""
    from server import main as server_main
    import asyncio
    
    try:
        asyncio.run(server_main())
        return 0
    except KeyboardInterrupt:
        print("\nServer stopped.")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1


def cmd_setup(args):
    """Setup command - verify setup"""
    from setup import main as setup_main
    return setup_main()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='MCP RAG Server - Unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp index                    # Index everything
  mcp index --docs             # Index docs only
  mcp index --code             # Index code only
  mcp index --cleanup          # Index + cleanup
  mcp stats                    # Show statistics
  mcp recover --all            # Recover deleted chunks
  mcp delete --preview         # Preview deletions
  mcp delete --confirm         # Confirm deletions
  mcp start                    # Start server
  mcp setup                    # Verify setup
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index documentation and code')
    index_parser.add_argument('--docs', action='store_true', help='Index documentation only')
    index_parser.add_argument('--code', action='store_true', help='Index code only')
    index_parser.add_argument('--cloud', action='store_true', help='Cloud collection only')
    index_parser.add_argument('--local', action='store_true', help='Local collection only')
    index_parser.add_argument('--cleanup', action='store_true', help='Clean up orphaned chunks (replaces --prune)')
    index_parser.set_defaults(func=cmd_index)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show collection statistics')
    stats_parser.add_argument('--cloud', action='store_true', help='Cloud collection only')
    stats_parser.add_argument('--local', action='store_true', help='Local collection only')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Recover command
    recover_parser = subparsers.add_parser('recover', help='Recover soft-deleted chunks')
    recover_parser.add_argument('--all', action='store_true', help='Recover all deleted chunks')
    recover_parser.add_argument('--file', help='Recover chunks for specific file')
    recover_parser.add_argument('--cloud', action='store_true', help='Cloud collection only')
    recover_parser.add_argument('--local', action='store_true', help='Local collection only')
    recover_parser.set_defaults(func=cmd_recover)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Permanently delete soft-deleted chunks')
    delete_parser.add_argument('--preview', action='store_true', help='Preview what would be deleted (safe)')
    delete_parser.add_argument('--confirm', action='store_true', help='Actually delete (requires confirmation)')
    delete_parser.add_argument('--file', help='Delete chunks for specific file only')
    delete_parser.add_argument('--cloud', action='store_true', help='Cloud collection only')
    delete_parser.add_argument('--local', action='store_true', help='Local collection only')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    delete_parser.set_defaults(func=cmd_delete)
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the MCP server')
    start_parser.set_defaults(func=cmd_start)
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Verify setup and configuration')
    setup_parser.set_defaults(func=cmd_setup)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())

