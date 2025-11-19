"""
Reranker: Re-rank search results using cross-encoder model.

This module improves retrieval accuracy by:
- Taking initial retrieval results (top 20-50)
- Re-scoring them with a cross-encoder model
- Returning top-ranked results (top 10)

Cross-encoders are more accurate than bi-encoders for ranking.
"""

import logging
from typing import List
from sentence_transformers import CrossEncoder

from .vector_store import SearchResult

logger = logging.getLogger(__name__)


class Reranker:
    """Re-rank search results using cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker with cross-encoder model.

        Args:
            model_name: Model name from HuggingFace

        Raises:
            RuntimeError: If model loading fails
        """
        self.model_name = model_name
        self._model = None
        logger.info(f"Reranker initialized with model: {model_name}")

    def _load_model(self) -> CrossEncoder:
        """
        Load cross-encoder model with error handling.

        Returns:
            Loaded CrossEncoder model

        Raises:
            RuntimeError: If model loading fails
        """
        if self._model is not None:
            return self._model

        try:
            logger.info(f"Loading reranking model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
            logger.info("✅ Reranking model loaded successfully")
            return self._model
        except Exception as e:
            logger.error(f"Failed to load reranking model: {str(e)}")
            raise RuntimeError(f"Failed to load reranking model: {str(e)}") from e

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 10,
    ) -> List[SearchResult]:
        """
        Re-rank search results based on relevance to query.

        Args:
            query: Search query
            results: Initial search results to rerank
            top_k: Number of top results to return

        Returns:
            Reranked results (sorted by relevance)

        Raises:
            ValueError: If results list is empty
            RuntimeError: If reranking fails
        """
        if not results:
            raise ValueError("Cannot rerank empty results list")

        if len(results) <= top_k:
            logger.debug(f"Results count ({len(results)}) <= top_k ({top_k}), no reranking needed")
            return results

        try:
            model = self._load_model()

            # Prepare pairs for cross-encoder
            pairs = [[query, result.content] for result in results]

            logger.debug(f"Reranking {len(pairs)} results with query: {query[:100]}...")

            # Get scores from cross-encoder
            scores = model.predict(pairs)

            # Sort results by score
            scored_results = list(zip(results, scores))
            scored_results.sort(key=lambda x: x[1], reverse=True)

            # Return top-k
            reranked = [result for result, score in scored_results[:top_k]]

            logger.debug(f"Reranking complete: {len(reranked)} results returned")
            return reranked

        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            # Fall back to initial results sorted by vector score
            logger.warning("Falling back to vector scores")
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

    def batch_rerank(
        self,
        query: str,
        results_list: List[List[SearchResult]],
        top_k: int = 10,
    ) -> List[List[SearchResult]]:
        """
        Re-rank multiple result sets (batch processing).

        Args:
            query: Search query
            results_list: List of result lists to rerank
            top_k: Number of top results to return per list

        Returns:
            List of reranked result lists

        Raises:
            ValueError: If results_list is empty or contains empty lists
        """
        if not results_list:
            raise ValueError("Cannot rerank empty results list")

        reranked_list = []
        for results in results_list:
            if not results:
                reranked_list.append([])
            else:
                reranked_list.append(self.rerank(query, results, top_k))

        return reranked_list

    def clear_cache(self):
        """Clear cached model to free memory."""
        self._model = None
        logger.info("Reranker model cache cleared")

