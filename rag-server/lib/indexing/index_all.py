#!/usr/bin/env python3
"""
Index all documents and code from config paths (incremental updates).

Handles both documentation (.md files) and code (.py, .ts, .tsx, .js, .jsx files).

Usage:
    python index_all.py                    # Index everything
    python index_all.py --docs-only        # Docs only
    python index_all.py --code-only        # Code only
    python index_all.py --cloud            # Cloud collection only
    python index_all.py --local            # Local collection only
"""
import argparse
import sys
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from lib.indexing.indexer import index_all_documents
from lib.indexing.code_indexer import CodeIndexer
from lib.core.embedding_manager import EmbeddingManager
from lib.core.vector_store import HybridVectorStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Index all documents and code"""
    parser = argparse.ArgumentParser(description="Index project documentation and code")
    parser.add_argument("--docs-only", action="store_true", help="Index documentation only")
    parser.add_argument("--code-only", action="store_true", help="Index code only")
    parser.add_argument("--cloud", action="store_true", help="Cloud collection only")
    parser.add_argument("--local", action="store_true", help="Local collection only")
    parser.add_argument("--prune", action="store_true", help="Actually delete orphaned chunks (otherwise dry-run)")
    args = parser.parse_args()

    try:
        config = load_config()
        logger.info("✅ Config loaded successfully")
        logger.info(f"   Project root: {config.project_root}")
        
        store = HybridVectorStore(config)
        logger.info("✅ Vector store initialized")
        
        # Determine collections to update
        # Default: cloud only (local storage is disabled by default)
        collections = []
        if args.cloud:
            collections = ["cloud"]
        elif args.local:
            if not store.local_enabled:
                logger.error("Local storage is disabled. Cannot index to local collection. Enable it in config.local_qdrant.enabled")
                return 1
            collections = ["local"]
        else:
            # Default: cloud only
            collections = ["cloud"]
            # Only add local if explicitly enabled AND user wants both
            # (This script doesn't have a --both flag, so default is cloud only)

        # Determine what to index
        index_docs = not args.code_only
        index_code = not args.docs_only

        logger.info(f"🚀 Starting indexing...")
        logger.info(f"   Collections: {collections}")
        logger.info(f"   Index docs: {index_docs}, Index code: {index_code}")

        total_indexed = 0
        total_errors = 0

        # Index documentation
        if index_docs:
            logger.info("📚 Indexing documentation...")
            doc_results = index_all_documents(store, config)
            logger.info(f"   ✅ Docs indexed: {doc_results.get('cloud', 0) + doc_results.get('local', 0)}")
            logger.info(f"   ❌ Docs errors: {doc_results.get('errors', 0)}")
            total_indexed += doc_results.get('cloud', 0) + doc_results.get('local', 0)
            total_errors += doc_results.get('errors', 0)

        # Index code
        if index_code:
            logger.info("💻 Indexing code...")
            try:
                embedder_mgr = EmbeddingManager(
                    doc_model=config.embedding_models.doc,
                    code_model=config.embedding_models.code
                )
                code_indexer = CodeIndexer(store, embedder_mgr)

                code_indexed = 0
                code_errors = 0

                # Index each code path
                base_path = config.project_root
                logger.info(f"   Searching for code in: {base_path}")
                logger.info(f"   Patterns: {config.code_paths}")
                code_files_found = []
                for code_path in config.code_paths:
                    if code_path.startswith("**") or "*" in code_path:
                        # Glob pattern - expand it relative to project root
                        try:
                            expanded = list(base_path.glob(code_path))
                            if expanded:
                                logger.info(f"   Found {len(expanded)} files matching '{code_path}'")
                                code_files_found.extend(expanded)
                            else:
                                logger.warning(f"   No files found matching pattern: '{code_path}'")
                            for path in expanded:
                                if path.is_file():
                                    try:
                                        for collection in collections:
                                            code_indexer.index_file(str(path), collection)
                                        code_indexed += 1
                                    except Exception as e:
                                        logger.warning(f"Failed to index {path}: {e}")
                                        code_errors += 1
                        except Exception as e:
                            logger.warning(f"Failed to glob {code_path}: {e}")
                    else:
                        # Direct path - can be absolute or relative to project root
                        try:
                            code_path_obj = Path(code_path)
                            if not code_path_obj.is_absolute():
                                code_path_obj = base_path / code_path
                            
                            if code_path_obj.exists():
                                for collection in collections:
                                    code_indexer.index_file(str(code_path_obj), collection)
                                code_indexed += 1
                            else:
                                logger.warning(f"Code path not found: {code_path_obj}")
                        except Exception as e:
                            logger.warning(f"Failed to index {code_path}: {e}")
                            code_errors += 1

                if not code_files_found and code_indexed == 0:
                    logger.warning(f"   ⚠️  No code files found! Check your config.code_paths.")
                    logger.warning(f"   Project root: {base_path}")
                    logger.warning(f"   Patterns tried: {config.code_paths}")
                    logger.warning(f"   Tip: Use 'python rag_cli.py stats' to see what's configured")
                
                logger.info(f"   ✅ Code indexed: {code_indexed}")
                logger.info(f"   ❌ Code errors: {code_errors}")
                total_indexed += code_indexed
                total_errors += code_errors

            except Exception as e:
                logger.error(f"Code indexing failed: {e}")
                import traceback
                traceback.print_exc()
                total_errors += 1

        # Cleanup deleted files
        logger.info("\n🧹 Cleaning up deleted files...")
        existing_files = set()
        
        # Collect all existing file paths (normalize to forward slashes)
        base_path = config.project_root
        if index_docs:
            for pattern in config.cloud_docs:
                for file_path in base_path.glob(pattern):
                    if file_path.is_file() and file_path.suffix == '.md':
                        try:
                            # Always compute relative to base_path for consistency
                            rel_path = str(file_path.relative_to(base_path))
                            existing_files.add(rel_path.replace('\\', '/'))
                        except ValueError:
                            logger.warning(f"Could not get relative path for {file_path}")
        
        if index_code:
            for code_path in config.code_paths:
                if "*" in code_path:
                    for file_path in base_path.glob(code_path):
                        if file_path.is_file():
                            try:
                                rel_path = str(file_path.relative_to(base_path))
                                existing_files.add(rel_path.replace('\\', '/'))
                            except ValueError:
                                logger.warning(f"Could not get relative path for {file_path}")
                else:
                    # Direct path: resolve and compute relative
                    code_path_obj = Path(code_path)
                    if not code_path_obj.is_absolute():
                        code_path_obj = base_path / code_path
                    else:
                        code_path_obj = code_path_obj.resolve()
                    
                    if code_path_obj.exists() and code_path_obj.is_file():
                        try:
                            rel_path = str(code_path_obj.relative_to(base_path))
                            existing_files.add(rel_path.replace('\\', '/'))
                        except ValueError:
                            logger.warning(f"Could not get relative path for {code_path_obj}")
        
        # Cleanup orphaned files (soft-delete by default, requires --prune to mark as deleted)
        total_cleaned = 0
        for collection in collections:
            # Skip cleanup for local if it's disabled
            if collection == "local" and not store.local_enabled:
                continue
            # Default: dry_run=True (safe, only reports)
            # With --prune: dry_run=False (actually marks as deleted)
            cleaned = store.cleanup_deleted_files(existing_files, collection, dry_run=not args.prune)
            total_cleaned += cleaned

        # Print summary
        logger.info(f"\n✅ Indexing complete:")
        logger.info(f"   Total indexed: {total_indexed}")
        logger.info(f"   Total errors: {total_errors}")
        logger.info(f"   Cleaned up: {total_cleaned} chunks from deleted files")

        # Get collection stats
        stats = store.get_collection_stats()
        logger.info(f"\n📊 Collection Stats:")
        for collection, stat in stats.items():
            logger.info(f"   {collection}: {stat['count']} points")

        return 0

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
