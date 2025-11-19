"""
Query Analyzer: Classify query intent to optimize retrieval strategy.

This module identifies the user's intent from a query and returns:
- Query intent type (enumeration, explanation, code_search, comparison, factual)
- Optimized retrieval parameters
- Suggested synthesis strategy

This enables different retrieval and synthesis strategies for different query types.
"""

import logging
import re
from enum import Enum
from typing import NamedTuple, Optional

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent types and their characteristics."""

    ENUMERATION = "enumeration"  # "list all X", "how many Y" → Need complete sets
    EXPLANATION = "explanation"  # "what is X", "how does Y work" → Need coherent explanations
    CODE_SEARCH = "code_search"  # "show me code", "find function" → Need code chunks
    COMPARISON = "comparison"  # "difference between A and B" → Need both sides
    FACTUAL = "factual"  # "what is the value of X" → Need exact answer


class QueryAnalysis(NamedTuple):
    """Result of query analysis."""

    intent: QueryIntent
    confidence: float  # 0.0-1.0, how confident we are in the classification
    keywords: list[str]  # Relevant keywords found in query
    content_types: list[str]  # Suggested content types to search ("doc", "code", etc.)
    needs_expansion: bool  # Whether section-aware expansion would help
    needs_reranking: bool  # Whether reranking would help


class QueryAnalyzer:
    """Analyzes queries to determine intent and optimize retrieval."""

    # Pattern definitions for intent detection
    ENUMERATION_PATTERNS = [
        r"\blist\s+all\b",
        r"\bhow\s+many\b",
        r"\bwhat\s+are\s+all\b",
        r"\benumerate\b",
        r"\bshow\s+me\s+all\b",
        r"\bcomplete\s+list\b",
        r"\ball\s+of\s+the\b",
        r"\bgive\s+me\s+all\b",
    ]

    CODE_SEARCH_PATTERNS = [
        r"\bshow\s+me.*code\b",
        r"\bfind.*function\b",
        r"\bwhere\s+is.*implementation\b",
        r"\bcode\s+for\b",
        r"\bfind.*method\b",
        r"\bimplementation\s+of\b",
        r"\bhow\s+.*is.*implemented\b",
        r"\bclass.*definition\b",
        r"\bfunction.*signature\b",
    ]

    COMPARISON_PATTERNS = [
        r"\bdifference\s+between\b",
        r"\bcompare\b",
        r"\bvs\.\b",
        r"\bversus\b",
        r"\bvs\b",
        r"\bwhat\s+is\s+different\b",
        r"\bsimilarities\s+and\s+differences\b",
    ]

    EXPLANATION_PATTERNS = [
        r"\bwhat\s+is\b",
        r"\bexplain\b",
        r"\bhow\s+does\b",
        r"\bwhy\b",
        r"\bdescribe\b",
        r"\bwhat\s+does\b",
        r"\btell\s+me\s+about\b",
        r"\bwhat\s+are\s+the\b",
    ]

    def __init__(self):
        """Initialize query analyzer with compiled patterns."""
        logger.debug("QueryAnalyzer initialized")

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query to determine intent and optimization strategy.

        Args:
            query: User's query text

        Returns:
            QueryAnalysis with intent, confidence, and optimization suggestions

        Raises:
            ValueError: If query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query_lower = query.lower()
        query_len = len(query)

        # Check each intent type in order of priority
        intents_checked = []

        # Check for enumeration (highest priority - very specific)
        enum_matches = self._count_matches(query_lower, self.ENUMERATION_PATTERNS)
        if enum_matches > 0:
            return self._create_analysis(
                intent=QueryIntent.ENUMERATION,
                confidence=min(1.0, 0.9 + (enum_matches * 0.05)),
                keywords=self._extract_keywords(query_lower, self.ENUMERATION_PATTERNS),
                content_types=["doc"],
                needs_expansion=True,
                needs_reranking=True,
            )

        # Check for code search
        code_matches = self._count_matches(query_lower, self.CODE_SEARCH_PATTERNS)
        if code_matches > 0:
            return self._create_analysis(
                intent=QueryIntent.CODE_SEARCH,
                confidence=min(1.0, 0.9 + (code_matches * 0.05)),
                keywords=self._extract_keywords(query_lower, self.CODE_SEARCH_PATTERNS),
                content_types=["code", "doc"],
                needs_expansion=False,
                needs_reranking=True,
            )

        # Check for comparison
        comp_matches = self._count_matches(query_lower, self.COMPARISON_PATTERNS)
        if comp_matches > 0:
            return self._create_analysis(
                intent=QueryIntent.COMPARISON,
                confidence=min(1.0, 0.85 + (comp_matches * 0.05)),
                keywords=self._extract_keywords(query_lower, self.COMPARISON_PATTERNS),
                content_types=["doc", "code"],
                needs_expansion=True,
                needs_reranking=True,
            )

        # Check for explanation
        expl_matches = self._count_matches(query_lower, self.EXPLANATION_PATTERNS)
        if expl_matches > 0:
            return self._create_analysis(
                intent=QueryIntent.EXPLANATION,
                confidence=min(1.0, 0.80 + (expl_matches * 0.05)),
                keywords=self._extract_keywords(query_lower, self.EXPLANATION_PATTERNS),
                content_types=["doc"],
                needs_expansion=True,
                needs_reranking=True,
            )

        # Default to factual query
        return self._create_analysis(
            intent=QueryIntent.FACTUAL,
            confidence=0.5,
            keywords=self._extract_keywords(query_lower, self.EXPLANATION_PATTERNS),
            content_types=["doc", "code"],
            needs_expansion=False,
            needs_reranking=True,
        )

    def _count_matches(self, text: str, patterns: list[str]) -> int:
        """
        Count how many patterns match in text.

        Args:
            text: Text to search
            patterns: List of regex patterns

        Returns:
            Number of pattern matches (with deduplication)
        """
        matches = set()
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    matches.add(pattern)
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {pattern}, error: {e}")

        return len(matches)

    def _extract_keywords(self, query: str, patterns: list[str]) -> list[str]:
        """
        Extract keywords that matched patterns from query.

        Args:
            query: Query text
            patterns: List of regex patterns

        Returns:
            List of matched keywords/phrases
        """
        keywords = []
        for pattern in patterns:
            try:
                matches = re.findall(pattern, query, re.IGNORECASE)
                keywords.extend(matches)
            except re.error:
                pass

        return list(dict.fromkeys(keywords))  # Deduplicate while preserving order

    def _create_analysis(
        self,
        intent: QueryIntent,
        confidence: float,
        keywords: list[str],
        content_types: list[str],
        needs_expansion: bool,
        needs_reranking: bool,
    ) -> QueryAnalysis:
        """
        Create query analysis result with logging.

        Args:
            intent: Query intent
            confidence: Confidence score (0.0-1.0)
            keywords: Relevant keywords
            content_types: Suggested content types to search
            needs_expansion: Whether section-aware expansion would help
            needs_reranking: Whether reranking would help

        Returns:
            QueryAnalysis result
        """
        analysis = QueryAnalysis(
            intent=intent,
            confidence=min(1.0, max(0.0, confidence)),
            keywords=keywords,
            content_types=content_types,
            needs_expansion=needs_expansion,
            needs_reranking=needs_reranking,
        )

        logger.debug(
            f"Query intent analysis: intent={intent.value}, confidence={analysis.confidence:.2f}, "
            f"keywords={keywords}, content_types={content_types}"
        )

        return analysis

