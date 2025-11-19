"""
Embedding Manager: Manage separate embedding models for documents and code.

This module handles:
- Loading and caching embedding models (MiniLM for docs, CodeBERT for code)
- Routing embeddings based on content type
- Error handling for model loading failures
- Performance optimization with model caching
"""

import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages dual embedding system: separate models for docs and code."""

    def __init__(self, doc_model: str, code_model: str):
        """
        Initialize embedding manager with separate models.

        Args:
            doc_model: Model name for document embeddings (e.g., "sentence-transformers/all-MiniLM-L6-v2")
            code_model: Model name for code embeddings (e.g., "microsoft/codebert-base")

        Raises:
            RuntimeError: If model loading fails
        """
        self.doc_model_name = doc_model
        self.code_model_name = code_model

        # Lazy-loaded model instances
        self._doc_embedder: Optional[SentenceTransformer] = None
        self._code_embedder: Optional[SentenceTransformer] = None

        logger.info(f"EmbeddingManager initialized with doc_model={doc_model}, code_model={code_model}")

    def get_embedder(self, content_type: str) -> SentenceTransformer:
        """
        Get embedder for content type (doc or code).

        Args:
            content_type: Either "doc" or "code"

        Returns:
            Loaded SentenceTransformer model

        Raises:
            ValueError: If content_type is invalid
            RuntimeError: If model loading fails
        """
        if content_type == "doc":
            if self._doc_embedder is None:
                self._doc_embedder = self._load_model(self.doc_model_name, "doc")
            return self._doc_embedder
        elif content_type == "code":
            if self._code_embedder is None:
                self._code_embedder = self._load_model(self.code_model_name, "code")
            return self._code_embedder
        else:
            raise ValueError(f"Invalid content_type: {content_type}. Must be 'doc' or 'code'.")

    def _load_model(self, model_name: str, model_type: str) -> SentenceTransformer:
        """
        Load embedding model with error handling.

        Args:
            model_name: Hugging Face model identifier
            model_type: Type of model ("doc" or "code") for logging

        Returns:
            Loaded SentenceTransformer model

        Raises:
            RuntimeError: If model loading fails
        """
        try:
            logger.info(f"Loading {model_type} embedding model: {model_name}")
            model = SentenceTransformer(model_name)
            logger.info(f"✅ {model_type} embedding model loaded successfully (vector size: {model.get_sentence_embedding_dimension()})")
            return model
        except Exception as e:
            logger.error(f"Failed to load {model_type} embedding model {model_name}: {str(e)}")
            raise RuntimeError(f"Failed to load {model_type} embedding model: {str(e)}") from e

    def embed_doc(self, content: str, show_progress_bar: bool = False) -> List[float]:
        """
        Embed document content.

        Args:
            content: Document text to embed
            show_progress_bar: Whether to show progress bar

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If content is empty
            RuntimeError: If embedding fails
        """
        if not content or not content.strip():
            raise ValueError("Cannot embed empty content")

        try:
            embedder = self.get_embedder("doc")
            embedding = embedder.encode(content, show_progress_bar=show_progress_bar)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to embed document: {str(e)}")
            raise RuntimeError(f"Failed to embed document: {str(e)}") from e

    def embed_code(self, content: str, show_progress_bar: bool = False) -> List[float]:
        """
        Embed code content.

        Args:
            content: Code text to embed
            show_progress_bar: Whether to show progress bar

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If content is empty
            RuntimeError: If embedding fails
        """
        if not content or not content.strip():
            raise ValueError("Cannot embed empty content")

        try:
            embedder = self.get_embedder("code")
            embedding = embedder.encode(content, show_progress_bar=show_progress_bar)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to embed code: {str(e)}")
            raise RuntimeError(f"Failed to embed code: {str(e)}") from e

    def embed_by_type(self, content: str, content_type: str, show_progress_bar: bool = False) -> List[float]:
        """
        Route to correct embedder based on content type.

        Args:
            content: Text to embed
            content_type: Either "doc" or "code"
            show_progress_bar: Whether to show progress bar

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If content_type is invalid or content is empty
            RuntimeError: If embedding fails
        """
        if not content or not content.strip():
            raise ValueError("Cannot embed empty content")

        if content_type == "doc":
            return self.embed_doc(content, show_progress_bar)
        elif content_type == "code":
            return self.embed_code(content, show_progress_bar)
        else:
            raise ValueError(f"Invalid content_type: {content_type}. Must be 'doc' or 'code'.")

    def get_vector_size(self, content_type: str = "doc") -> int:
        """
        Get embedding vector size for content type.

        Args:
            content_type: Either "doc" or "code"

        Returns:
            Vector size (dimensionality) of embeddings

        Raises:
            ValueError: If content_type is invalid
        """
        embedder = self.get_embedder(content_type)
        return embedder.get_sentence_embedding_dimension()

    def clear_cache(self):
        """Clear cached models to free memory."""
        self._doc_embedder = None
        self._code_embedder = None
        logger.info("Embedding model cache cleared")

