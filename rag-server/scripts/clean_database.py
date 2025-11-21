#!/usr/bin/env python3
"""
Clean all data from Qdrant database collections.
⚠️  WARNING: This permanently deletes all indexed data!
"""
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


def clean_collection(store, collection_name, collection_type):
    """Delete all points from a collection"""
    try:
        if collection_type == "cloud":
            client = store.cloud_client
        elif collection_type == "local":
            if not store.local_enabled:
                logger.warning(f"Local storage is disabled. Skipping cleanup for local collection.")
                return True
            client = store.local_client
        else:
            raise ValueError(f"Invalid collection type: {collection_type}")
        
        # Get collection info
        try:
            collection_info = client.get_collection(collection_name)
            count = collection_info.points_count
            logger.info(f"  Found {count:,} points in {collection_name}")
            
            if count > 0:
                # Delete all points
                client.delete(
                    collection_name=collection_name,
                    points_selector={"all": True}
                )
                logger.info(f"  [OK] Deleted all {count:,} points from {collection_name}")
            else:
                logger.info(f"  [OK] Collection {collection_name} is already empty")
        except Exception as e:
            logger.warning(f"  Collection {collection_name} may not exist: {e}")
            
    except Exception as e:
        logger.error(f"  [ERROR] Failed to clean {collection_name}: {e}")
        return False
    return True


def main():
    """Clean all collections"""
    print("=" * 60)
    print("Database Cleanup - Delete All Indexed Data")
    print("=" * 60)
    print()
    print("WARNING: This will permanently delete ALL indexed data!")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        return 0
    
    try:
        config = load_config()
        logger.info("[OK] Config loaded")
        
        store = HybridVectorStore(config)
        logger.info("[OK] Vector store initialized")
        print()
        
        # Clean cloud collection
        print("Cleaning cloud collection...")
        clean_collection(store, config.cloud_qdrant.collection, "cloud")
        
        # Clean local collection (only if enabled)
        if store.local_enabled:
            print("\nCleaning local collection...")
            clean_collection(store, config.local_qdrant.collection, "local")
        else:
            print("\nSkipping local collection (disabled in config)")
        
        print()
        print("=" * 60)
        print("[OK] Database cleanup complete!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

