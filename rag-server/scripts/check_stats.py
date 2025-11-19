#!/usr/bin/env python3
"""
Check Qdrant collection statistics - see how many chunks are indexed.

Usage:
    python check_stats.py          # Check both cloud and local
    python check_stats.py --cloud  # Cloud only
    python check_stats.py --local  # Local only
"""
import argparse
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from lib.core.vector_store import HybridVectorStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Check collection statistics"""
    parser = argparse.ArgumentParser(description="Check Qdrant collection statistics")
    parser.add_argument("--cloud", action="store_true", help="Cloud collection only")
    parser.add_argument("--local", action="store_true", help="Local collection only")
    args = parser.parse_args()

    try:
        config = load_config()
        store = HybridVectorStore(config)
        
        stats = store.get_collection_stats()
        
        print("\n" + "="*60)
        print("Qdrant Collection Statistics")
        print("="*60)
        
        if args.cloud:
            print(f"\nCloud Collection: {config.cloud_qdrant.collection}")
            print(f"   Chunks: {stats['cloud']['count']:,}")
        elif args.local:
            print(f"\nLocal Collection: {config.local_qdrant.collection}")
            print(f"   Chunks: {stats['local']['count']:,}")
        else:
            print(f"\nCloud Collection: {config.cloud_qdrant.collection}")
            print(f"   Chunks: {stats['cloud']['count']:,}")
            print(f"\nLocal Collection: {config.local_qdrant.collection}")
            print(f"   Chunks: {stats['local']['count']:,}")
            print(f"\nTotal Chunks: {stats['cloud']['count'] + stats['local']['count']:,}")
        
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

