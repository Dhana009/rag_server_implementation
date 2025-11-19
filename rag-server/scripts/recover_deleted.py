#!/usr/bin/env python3
"""
Recover soft-deleted chunks - unmark chunks that were marked as deleted.

Usage:
    python recover_deleted.py              # Show deleted chunks count
    python recover_deleted.py --recover    # Unmark all deleted chunks
    python recover_deleted.py --file <path> # Recover chunks for specific file
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
    """Recover soft-deleted chunks"""
    parser = argparse.ArgumentParser(description="Recover soft-deleted chunks")
    parser.add_argument("--recover", action="store_true", help="Actually unmark deleted chunks")
    parser.add_argument("--file", help="Recover chunks for specific file path")
    parser.add_argument("--cloud", action="store_true", help="Cloud collection only")
    parser.add_argument("--local", action="store_true", help="Local collection only")
    args = parser.parse_args()

    try:
        config = load_config()
        store = HybridVectorStore(config)
        
        collections = []
        if args.cloud:
            collections = ["cloud"]
        elif args.local:
            collections = ["local"]
        else:
            collections = ["cloud", "local"]
        
        total_deleted = 0
        total_recovered = 0
        
        for collection in collections:
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
            total_deleted += deleted_count
            
            logger.info(f"\n📊 {collection.upper()} Collection:")
            logger.info(f"   Deleted chunks: {deleted_count:,}")
            
            if args.recover and deleted_count > 0:
                # Unmark deleted chunks (batch update for efficiency)
                point_ids = [p.id for p in points]
                batch_size = 1000
                recovered_count = 0
                
                for i in range(0, len(point_ids), batch_size):
                    batch = point_ids[i:i + batch_size]
                    try:
                        client.set_payload(
                            collection_name=coll_name,
                            payload={"is_deleted": False},
                            points=batch  # Batch update - much faster!
                        )
                        recovered_count += len(batch)
                    except Exception as e:
                        logger.warning(f"Failed to recover batch {i//batch_size + 1}: {e}")
                        # Fallback: try individual updates for this batch
                        for point_id in batch:
                            try:
                                client.set_payload(
                                    collection_name=coll_name,
                                    payload={"is_deleted": False},
                                    points=[point_id]
                                )
                                recovered_count += 1
                            except Exception as e2:
                                logger.warning(f"Failed to recover point {point_id}: {e2}")
                
                logger.info(f"   ✅ Recovered {recovered_count:,} chunks")
                total_recovered += recovered_count
        
        print("\n" + "="*60)
        if args.recover:
            print(f"✅ Recovery Complete:")
            print(f"   Total recovered: {total_recovered:,} chunks")
        else:
            print(f"📊 Deleted Chunks Summary:")
            print(f"   Total deleted: {total_deleted:,} chunks")
            print(f"\n💡 To recover, run: python recover_deleted.py --recover")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

