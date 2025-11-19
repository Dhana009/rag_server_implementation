"""
Enhanced Search Tool: Search documentation and code with filtering.

Supports:
- Content type filtering (doc, code)
- Language filtering (python, typescript, etc.)
- Detailed results with metadata
"""

import logging
import time
from mcp.types import Tool

logger = logging.getLogger(__name__)

try:
    from ..core.vector_store import HybridVectorStore
    from ..core.embedding_manager import EmbeddingManager
    from ..config import load_config
    from ..utils.citation import format_citation
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.core.vector_store import HybridVectorStore
    from lib.core.embedding_manager import EmbeddingManager
    from config import load_config
    from lib.utils.citation import format_citation


def search_tool(
    query: str,
    content_type: str = "all",
    language: str = "all",
    top_k: int = 10
) -> str:
    """
    Enhanced search with filtering and detailed results.

    Args:
        query: Search query
        content_type: "doc", "code", or "all"
        language: "python", "typescript", "all"
        top_k: Number of results

    Returns:
        Formatted search results with metadata
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        embedder_mgr = EmbeddingManager(
            doc_model=config.embedding_models.doc,
            code_model=config.embedding_models.code
        )

        # Choose embedder based on content type
        if content_type == "code":
            embedder = embedder_mgr.get_embedder("code")
        else:
            embedder = embedder_mgr.get_embedder("doc")

        # Perform search
        logger.debug(f"Search: query='{query}', type={content_type}, lang={language}, top_k={top_k}")
        
        results = store.hybrid_search(
            query=query,
            embedder=embedder,
            top_k=top_k
        )
        
        if not results:
            return f"No results found for: '{query}'"
        
        # Filter results
        filtered_results = []
        for result in results:
            # Filter by content type
            if content_type != "all":
                result_type = result.metadata.get("content_type", "doc")
                if result_type != content_type:
                    continue

            # Filter by language
            if language != "all":
                result_lang = result.metadata.get("language", "unknown")
                if result_lang != language:
                    continue

            filtered_results.append(result)

        if not filtered_results:
            return f"No results matching filters: type={content_type}, language={language}"

        # Format results
        answer = f"**Search Results for: '{query}'** ({len(filtered_results)} found)\n\n"

        for i, result in enumerate(filtered_results[:top_k], 1):
            citation = format_citation(result.file_path, result.line_number)
            content_type_label = result.metadata.get("content_type", "text")
            score = result.score

            # Format content preview (first 500 chars)
            preview = result.content[:500].replace('\n', ' ')

            answer += f"**{i}. {citation}** (Score: {score:.2f}, Type: {content_type_label})\n"
            answer += f"{preview}{'...' if len(result.content) > 500 else ''}\n\n"

        # Add metadata summary
        answer += "---\n"
        answer += f"**Search Summary:**\n"
        answer += f"- Results: {len(filtered_results)} of {len(results)} total\n"
        answer += f"- Content Type: {content_type}\n"
        answer += f"- Language: {language}\n"

        elapsed = time.time() - start_time
        logger.info(f"✅ search_tool completed in {elapsed:.2f}s: {len(filtered_results)} results (type={content_type}, lang={language})")
        logger.debug(f"Search complete: {len(filtered_results)} results returned")
        return answer

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ search_tool failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return f"Search error: {str(e)}"


def code_search_tool(
    query: str,
    language: str = "all",
    code_type: str = "all",
    top_k: int = 10
) -> str:
    """
    Specialized code search with language and code type filtering.

    Args:
        query: Search query for code
        language: "python", "typescript", "all"
        code_type: "function", "class", "method", "all"
        top_k: Number of results

    Returns:
        Formatted code search results
    """
    try:
        config = load_config()
        store = HybridVectorStore(config)
        embedder_mgr = EmbeddingManager(
            doc_model=config.embedding_models.doc,
            code_model=config.embedding_models.code
        )

        # Use code embedder
        code_embedder = embedder_mgr.get_embedder("code")

        logger.debug(f"Code search: query='{query}', lang={language}, type={code_type}, top_k={top_k}")

        results = store.hybrid_search(
            query=query,
            embedder=code_embedder,
            top_k=top_k
        )

        if not results:
            return f"No code found matching: '{query}'"

        # Filter by language and code type
        filtered_results = []
        for result in results:
            # Check content type is code
            if result.metadata.get("content_type") != "code":
                continue

            # Filter by language
            if language != "all":
                result_lang = result.metadata.get("language", "unknown")
                if result_lang != language:
                    continue

            # Filter by code type (function, class, method)
            if code_type != "all":
                result_type = result.metadata.get("code_type", "function")
                if result_type != code_type:
                    continue

            filtered_results.append(result)

        if not filtered_results:
            return f"No code found matching: '{query}' (language={language}, type={code_type})"

        # Format results
        answer = f"**Code Search Results for: '{query}'**\n\n"

        # Group by file and language
        by_file = {}
        for result in filtered_results:
            file_path = result.file_path
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(result)

        for file_path, file_results in sorted(by_file.items())[:5]:  # Top 5 files
            lang = file_results[0].metadata.get("language", "unknown")
            answer += f"**File: {file_path}** ({lang})\n\n"

            for result in file_results[:3]:  # Top 3 per file
                code_name = result.metadata.get("name", "Unknown")
                code_type_name = result.metadata.get("code_type", "code")
                lines = result.line_number

                answer += f"- **{code_type_name}: {code_name}** (line {lines})\n"
                answer += f"```{lang}\n{result.content}\n```\n\n"

        answer += "---\n"
        answer += f"Found {len(filtered_results)} code elements matching your query\n"

        logger.debug(f"Code search complete: {len(filtered_results)} results")
        return answer

    except Exception as e:
        logger.error(f"Code search error: {str(e)}", exc_info=True)
        return f"Code search error: {str(e)}"


# MCP Tool definition
search_tool_mcp = Tool(
    name="search",
    description="Semantic search across all project documentation. Returns relevant chunks with file:line citations.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g., 'selector policy', 'flow-4 implementation', 'architecture rules')"
            },
            "content_type": {
                "type": "string",
                "description": "Filter by content type: 'doc', 'code', or 'all'",
                "enum": ["doc", "code", "all"],
                "default": "all"
            },
            "language": {
                "type": "string",
                "description": "Filter by language: 'python', 'typescript', 'markdown', or 'all'",
                "enum": ["python", "typescript", "markdown", "all"],
                "default": "all"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }
)
