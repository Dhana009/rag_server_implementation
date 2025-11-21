#!/usr/bin/env python3
"""
Permanently delete soft-deleted chunks - physically remove chunks marked as deleted.

⚠️  WARNING: This permanently deletes chunks. They cannot be recovered after this.

Usage:
    python permanent_delete.py --preview    # Show what would be deleted (safe)
    python permanent_delete.py --delete     # Actually delete (requires confirmation)
    python permanent_delete.py --file <path> # Delete chunks for specific file only
"""
import argparse
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from lib.core.vector_store import HybridVectorStore
from qdrant_client.models import Filter, FieldCondition, MatchValue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Permanently delete soft-deleted chunks"""
    parser = argparse.ArgumentParser(description="Permanently delete soft-deleted chunks")
    parser.add_argument("--preview", action="store_true", help="Preview what would be deleted (safe)")
    parser.add_argument("--delete", action="store_true", help="Actually delete (requires confirmation)")
    parser.add_argument("--file", help="Delete chunks for specific file path only")
    parser.add_argument("--cloud", action="store_true", help="Cloud collection only")
    parser.add_argument("--local", action="store_true", help="Local collection only")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if not args.preview and not args.delete:
        parser.error("Must specify either --preview or --delete")

    try:
        config = load_config()
        store = HybridVectorStore(config)
        
        collections = []
        if args.cloud:
            collections = ["cloud"]
        elif args.local:
            if not store.local_enabled:
                logger.error("Local storage is disabled. Cannot delete from local collection. Enable it in config.local_qdrant.enabled")
                return 1
            collections = ["local"]
        else:
            collections = ["cloud"]
            if store.local_enabled:
                collections.append("local")
            else:
                logger.info("Local storage is disabled. Deleting from cloud only.")
        
        total_deleted = 0
        points_to_delete = {}
        
        for collection in collections:
            # Skip if local is disabled
            if collection == "local" and not store.local_enabled:
                continue
            client = store.cloud_client if collection == "cloud" else store.local_client
            coll_name = store.cloud_collection if collection == "cloud" else store.local_collection
            
            # Build filter (no boolean filter - we'll filter in Python)
            # For cloud Qdrant, we can't filter by boolean is_deleted in query
            if args.file:
                # Filter by file path only
                filter_condition = Filter(
                    must=[
                        FieldCondition(key="file_path", match=MatchValue(value=args.file))
                    ]
                )
                points, _ = client.scroll(
                    collection_name=coll_name,
                    scroll_filter=filter_condition,
                    limit=100000,
                    with_payload=True,
                    with_vectors=False
                )
            else:
                # Get all points, filter in Python
                points, _ = client.scroll(
                    collection_name=coll_name,
                    limit=100000,
                    with_payload=True,
                    with_vectors=False
                )
            
            # Filter for deleted chunks in Python (avoids boolean index requirement)
            points = [p for p in points if p.payload.get('is_deleted', False) == True]
            
            deleted_count = len(points)
            points_to_delete[collection] = [p.id for p in points]
            total_deleted += deleted_count
            
            logger.info(f"\n📊 {collection.upper()} Collection:")
            logger.info(f"   Soft-deleted chunks: {deleted_count:,}")
            
            if args.file:
                logger.info(f"   File filter: {args.file}")
        
        print("\n" + "="*60)
        print(f"📊 Soft-Deleted Chunks Summary:")
        print(f"   Total to delete: {total_deleted:,} chunks")
        print("="*60)
        
        if args.preview:
            print("\n💡 This is a preview. No chunks were deleted.")
            print("   To actually delete, run: python permanent_delete.py --delete")
            return 0
        
        if args.delete:
            if not args.force:
                print("\n⚠️  WARNING: This will PERMANENTLY DELETE chunks!")
                print("   This action cannot be undone.")
                response = input(f"\n   Delete {total_deleted:,} chunks? (yes/no): ")
                if response.lower() != "yes":
                    print("   Cancelled.")
                    return 0
            
            # Actually delete
            deleted_count = 0
            for collection in collections:
                # Skip if local is disabled
                if collection == "local" and not store.local_enabled:
                    continue
                if points_to_delete.get(collection):
                    client = store.cloud_client if collection == "cloud" else store.local_client
                    coll_name = store.cloud_collection if collection == "cloud" else store.local_collection
                    
                    try:
                        client.delete(
                            collection_name=coll_name,
                            points_selector=points_to_delete[collection]
                        )
                        count = len(points_to_delete[collection])
                        logger.info(f"   ✅ Permanently deleted {count:,} chunks from {collection}")
                        deleted_count += count
                    except Exception as e:
                        logger.error(f"   ❌ Failed to delete from {collection}: {e}")
            
            print("\n" + "="*60)
            print(f"✅ Permanent Deletion Complete:")
            print(f"   Total deleted: {deleted_count:,} chunks")
            print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

