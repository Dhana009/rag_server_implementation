"""
Code Indexer: Index code files into vector store.

Handles:
- Parsing code files using CodeParser
- Chunking using CodeChunker
- Embedding with CodeBERT
- Storing in Qdrant with metadata
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.indexing.code_parser import CodeParser
from lib.indexing.code_chunker import CodeChunker
from lib.core.embedding_manager import EmbeddingManager
from lib.core.vector_store import HybridVectorStore
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


class CodeIndexer:
    """Index code files into vector store."""

    def __init__(self, vector_store: HybridVectorStore, embedding_manager: EmbeddingManager):
        """
        Initialize code indexer.

        Args:
            vector_store: HybridVectorStore instance
            embedding_manager: EmbeddingManager instance for code embeddings
        """
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
        self.parser = CodeParser()
        self.chunker = CodeChunker()

    def index_file(self, file_path: str, collection: str = "local") -> bool:
        """
        Index a single code file.

        Args:
            file_path: Path to code file
            collection: "cloud" or "local"

        Returns:
            True if successful

        Raises:
            ValueError: If file not supported
            RuntimeError: If indexing fails
        """
        try:
            logger.info(f"Indexing code file: {file_path}")

            # Parse file
            parsed_elements = self.parser.parse_file(file_path)
            if not parsed_elements:
                logger.warning(f"No elements parsed from {file_path}")
                return False

            # Get file content
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Chunk
            chunks = self.chunker.chunk_code(parsed_elements, file_content)
            if not chunks:
                logger.warning(f"No chunks created from {file_path}")
                return False

            # Determine language
            language = Path(file_path).suffix.lower()
            if language in [".py"]:
                language = "python"
            elif language in [".ts", ".tsx", ".js", ".jsx"]:
                language = "typescript"
            else:
                language = "unknown"

            # Embed chunks using code embedder
            code_embedder = self.embedding_manager.get_embedder("code")

            # Convert chunks to format for vector_store.index_doc
            formatted_chunks = []
            for chunk in chunks:
                formatted_chunks.append({
                    "content": chunk["content"],
                    "line_start": chunk["start_line"],
                    "line_end": chunk["end_line"],
                    "metadata": {
                        **chunk["metadata"],
                        "language": language,
                        "code_type": chunk["metadata"].get("code_type", "function")
                    }
                })

            # Index in vector store
            success = self.vector_store.index_doc(file_path, collection, formatted_chunks)

            if success:
                logger.info(f"✅ Indexed {len(formatted_chunks)} code chunks from {file_path}")
            else:
                logger.error(f"Failed to index {file_path}")

            return success

        except Exception as e:
            logger.error(f"Code indexing failed for {file_path}: {str(e)}")
            raise RuntimeError(f"Code indexing failed: {str(e)}") from e

    def index_directory(self, directory: str, collection: str = "local", recursive: bool = True) -> Dict[str, int]:
        """
        Index all code files in a directory.

        Args:
            directory: Path to directory
            collection: "cloud" or "local"
            recursive: Whether to search recursively

        Returns:
            Dict with counts: {"indexed": N, "failed": N, "skipped": N}

        Raises:
            ValueError: If directory doesn't exist
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        results = {"indexed": 0, "failed": 0, "skipped": 0}

        # Supported extensions
        supported = {".py", ".ts", ".tsx", ".js", ".jsx"}

        # Find all code files
        pattern = "**/*" if recursive else "*"
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue

            if file_path.suffix not in supported:
                results["skipped"] += 1
                continue

            try:
                if self.index_file(str(file_path), collection):
                    results["indexed"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.warning(f"Failed to index {file_path}: {e}")
                results["failed"] += 1

        logger.info(f"Directory indexing complete: {results['indexed']} indexed, {results['failed']} failed, {results['skipped']} skipped")
        return results

