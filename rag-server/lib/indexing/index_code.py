#!/usr/bin/env python3
"""
Index code files only (for incremental code indexing).

Usage:
    python index_code.py <file_path>      # Index single file
    python index_code.py <dir_path>       # Index all code in directory
    python index_code.py --update         # Update from config code_paths
"""
import argparse
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from lib.indexing.code_indexer import CodeIndexer
from lib.core.embedding_manager import EmbeddingManager
from lib.core.vector_store import HybridVectorStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Index code files"""
    parser = argparse.ArgumentParser(description="Index code files")
    parser.add_argument("path", nargs="?", help="File or directory path to index")
    parser.add_argument("--update", action="store_true", help="Update from config code_paths")
    parser.add_argument("--collection", default="local", help="Collection: 'cloud' or 'local'")
    args = parser.parse_args()

    try:
        config = load_config()
        logger.info("✅ Config loaded")
        
        store = HybridVectorStore(config)
        logger.info("✅ Vector store initialized")
        
        embedder_mgr = EmbeddingManager(
            doc_model=config.embedding_models.doc,
            code_model=config.embedding_models.code
        )
        logger.info("✅ Embedding manager initialized")
        
        code_indexer = CodeIndexer(store, embedder_mgr)

        total_indexed = 0
        total_errors = 0

        if args.update:
            # Index from config paths
            logger.info("💻 Indexing code from config paths...")
            for code_path in config.code_paths:
                try:
                    code_path_obj = Path(code_path)
                    if code_path_obj.is_file():
                        logger.info(f"Indexing file: {code_path}")
                        if code_indexer.index_file(code_path, args.collection):
                            total_indexed += 1
                        else:
                            total_errors += 1
                    elif code_path_obj.is_dir():
                        logger.info(f"Indexing directory: {code_path}")
                        results = code_indexer.index_directory(code_path, args.collection)
                        total_indexed += results["indexed"]
                        total_errors += results["failed"]
                except Exception as e:
                    logger.warning(f"Failed to index {code_path}: {e}")
                    total_errors += 1

        elif args.path:
            # Index specific path
            path_obj = Path(args.path)
            if not path_obj.exists():
                logger.error(f"Path not found: {args.path}")
                return 1

            if path_obj.is_file():
                logger.info(f"💻 Indexing file: {args.path}")
                if code_indexer.index_file(args.path, args.collection):
                    total_indexed = 1
                else:
                    total_errors = 1

            elif path_obj.is_dir():
                logger.info(f"💻 Indexing directory: {args.path}")
                results = code_indexer.index_directory(args.path, args.collection)
                total_indexed = results["indexed"]
                total_errors = results["failed"]
        else:
            logger.error("Please provide a path or use --update")
            parser.print_help()
            return 1

        # Print summary
        logger.info(f"\n✅ Code indexing complete:")
        logger.info(f"   Indexed: {total_indexed}")
        logger.info(f"   Errors: {total_errors}")

        # Get collection stats
        stats = store.get_collection_stats()
        logger.info(f"\n📊 Collection Stats:")
        for collection, stat in stats.items():
            logger.info(f"   {collection}: {stat['count']} points")

        return 0 if total_errors == 0 else 1

    except Exception as e:
        logger.error(f"Code indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

