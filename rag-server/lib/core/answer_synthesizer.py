"""
Answer Synthesizer: Synthesize complete answers from retrieved chunks.

This module reconstructs complete, coherent answers based on query intent:
- Enumeration: Reconstruct complete numbered lists
- Explanation: Merge related chunks in document order
- Code Search: Format code with context and imports
- Comparison: Organize side-by-side or sequential comparison
"""

import logging
import re
from enum import Enum
from typing import List

from .query_analyzer import QueryIntent
from .vector_store import SearchResult

logger = logging.getLogger(__name__)


class AnswerSynthesizer:
    """Synthesize complete answers from retrieved chunks."""

    def synthesize(
        self,
        chunks: List[SearchResult],
        intent: QueryIntent,
        query: str = "",
    ) -> str:
        """
        Synthesize answer based on query intent and retrieved chunks.

        Args:
            chunks: Retrieved search results
            intent: Query intent (from query_analyzer)
            query: Original query (for context)

        Returns:
            Synthesized, complete answer

        Raises:
            ValueError: If chunks is empty
            RuntimeError: If synthesis fails
        """
        if not chunks:
            raise ValueError("Cannot synthesize answer from empty chunks")

        try:
            if intent == QueryIntent.ENUMERATION:
                return self._synthesize_enumeration(chunks, query)
            elif intent == QueryIntent.EXPLANATION:
                return self._synthesize_explanation(chunks, query)
            elif intent == QueryIntent.CODE_SEARCH:
                return self._synthesize_code_search(chunks, query)
            elif intent == QueryIntent.COMPARISON:
                return self._synthesize_comparison(chunks, query)
            else:  # FACTUAL
                return self._synthesize_factual(chunks, query)
        except Exception as e:
            logger.error(f"Synthesis failed for intent {intent}: {str(e)}")
            raise RuntimeError(f"Answer synthesis failed: {str(e)}") from e

    def _synthesize_enumeration(self, chunks: List[SearchResult], query: str) -> str:
        """
        Synthesize enumeration queries: reconstruct complete numbered lists.

        Strategy:
        1. Extract all numbered items from chunks
        2. Sort by number
        3. Deduplicate
        4. Verify completeness
        5. Format as complete list
        """
        logger.debug(f"Synthesizing enumeration for query: {query}")

        # Extract all numbered items
        items = {}
        for chunk in chunks:
            # Find numbered lists in content
            matches = re.findall(r'^(\d+)\.\s+(.+)$', chunk.content, re.MULTILINE)
            for num_str, item in matches:
                try:
                    num = int(num_str)
                    items[num] = item.strip()
                except ValueError:
                    pass

        if not items:
            # No numbered items found, return full content
            logger.warning("No numbered items found, returning full content")
            return "\n\n".join([c.content for c in chunks])

        # Sort by number and format
        sorted_nums = sorted(items.keys())
        answer_lines = []

        for num in sorted_nums:
            answer_lines.append(f"{num}. {items[num]}")

        # Check for gaps (incomplete list)
        if sorted_nums[-1] > len(sorted_nums):
            logger.warning(f"List may be incomplete: max number is {sorted_nums[-1]}, but only {len(sorted_nums)} items found")

        answer = "\n".join(answer_lines)
        logger.debug(f"Enumeration synthesis complete: {len(items)} items")
        return answer

    def _synthesize_explanation(self, chunks: List[SearchResult], query: str) -> str:
        """
        Synthesize explanation queries: merge chunks in document order.

        Strategy:
        1. Sort chunks by line number (maintain document order)
        2. Remove overlaps (deduplicate content)
        3. Merge related chunks
        4. Format as coherent explanation
        """
        logger.debug(f"Synthesizing explanation for query: {query}")

        # Sort by file and line number
        sorted_chunks = sorted(chunks, key=lambda x: (x.file_path, x.line_number))

        # Remove overlaps
        merged_content = []
        last_content = ""

        for chunk in sorted_chunks:
            # Check for significant overlap with previous chunk
            if last_content and chunk.content.startswith(last_content[-100:]):
                # Skip duplicate beginning
                overlap_len = min(100, len(last_content))
                chunk_content = chunk.content[overlap_len:]
            else:
                chunk_content = chunk.content

            merged_content.append(chunk_content)
            last_content = chunk_content

        # Format answer
        answer = "\n\n".join([c.strip() for c in merged_content if c.strip()])

        logger.debug(f"Explanation synthesis complete: {len(sorted_chunks)} chunks merged")
        return answer

    def _synthesize_code_search(self, chunks: List[SearchResult], query: str) -> str:
        """
        Synthesize code search queries: format code with context.

        Strategy:
        1. Group by file
        2. Preserve code formatting
        3. Include imports and context
        4. Add file paths and line numbers
        """
        logger.debug(f"Synthesizing code search for query: {query}")

        # Group by file
        files = {}
        for chunk in chunks:
            if chunk.file_path not in files:
                files[chunk.file_path] = []
            files[chunk.file_path].append(chunk)

        # Format answer
        sections = []

        for file_path, file_chunks in sorted(files.items()):
            sections.append(f"**File: {file_path}**\n")

            # Sort by line number
            file_chunks.sort(key=lambda x: x.line_number)

            for chunk in file_chunks:
                # Format as code block
                sections.append(f"Lines {chunk.line_number}:")
                sections.append(f"```\n{chunk.content}\n```\n")

        answer = "\n".join(sections)
        logger.debug(f"Code search synthesis complete: {len(files)} files, {len(chunks)} chunks")
        return answer

    def _synthesize_comparison(self, chunks: List[SearchResult], query: str) -> str:
        """
        Synthesize comparison queries: organize side-by-side.

        Strategy:
        1. Identify comparison pairs (A vs B)
        2. Separate chunks by topic
        3. Format for easy comparison
        """
        logger.debug(f"Synthesizing comparison for query: {query}")

        # For now, simple organization by section
        sections = {}
        for chunk in chunks:
            section = chunk.metadata.get("section", "Other")
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk)

        # Format answer
        answer_parts = []

        for section, section_chunks in sorted(sections.items()):
            answer_parts.append(f"## {section}\n")
            for chunk in section_chunks:
                answer_parts.append(chunk.content)
                answer_parts.append("")

        answer = "\n".join(answer_parts)
        logger.debug(f"Comparison synthesis complete: {len(sections)} sections")
        return answer

    def _synthesize_factual(self, chunks: List[SearchResult], query: str) -> str:
        """
        Synthesize factual queries: return most relevant chunk.

        Strategy:
        1. Take top chunk (most relevant)
        2. Extract fact/answer
        3. Return concisely
        """
        logger.debug(f"Synthesizing factual for query: {query}")

        if not chunks:
            return "No relevant information found."

        # Return top chunk
        answer = chunks[0].content

        logger.debug("Factual synthesis complete: returned top chunk")
        return answer

