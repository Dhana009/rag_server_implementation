from mcp.types import Tool
import logging
import time

logger = logging.getLogger(__name__)

try:
    from ..core.vector_store import HybridVectorStore
    from ..core.embedding_manager import EmbeddingManager
    from ..core.query_analyzer import QueryAnalyzer
    from ..core.reranker import Reranker
    from ..core.answer_synthesizer import AnswerSynthesizer
    from ..utils.citation import format_citation
    from ..config import load_config
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.core.vector_store import HybridVectorStore
    from lib.core.embedding_manager import EmbeddingManager
    from lib.core.query_analyzer import QueryAnalyzer
    from lib.core.reranker import Reranker
    from lib.core.answer_synthesizer import AnswerSynthesizer
    from lib.utils.citation import format_citation
    from config import load_config

def ask_tool(question: str, context: str = "") -> str:
    """
    Ask questions about the project with intelligent RAG pipeline.
    
    Pipeline:
    1. Query intent classification
    2. Hybrid retrieval (BM25 + Vector)
    3. Section-aware expansion
    4. Reranking
    5. Answer synthesis
    6. Return complete answer
    """
    start_time = time.time()
    try:
        # Load config and initialize components
        config = load_config()
        store = HybridVectorStore(config)
        embedder_mgr = EmbeddingManager(
            doc_model=config.embedding_models.doc,
            code_model=config.embedding_models.code
        )
        query_analyzer = QueryAnalyzer()
        reranker = Reranker(model_name=config.embedding_models.reranking)
        synthesizer = AnswerSynthesizer()

        search_query = f"{question} {context}".strip()

        # Step 1: Classify query intent
        analysis = query_analyzer.analyze(search_query)
        logger.info(f"Query intent: {analysis.intent.value} (confidence: {analysis.confidence:.2f})")

        # Step 2: Hybrid retrieval with section-aware expansion
        doc_embedder = embedder_mgr.get_embedder("doc")
        
        if analysis.needs_expansion:
            results = store.search_with_expansion(
                query=search_query,
                embedder=doc_embedder,
                top_k=config.hybrid_retrieval.search_top_k,
                rerank_top_k=config.hybrid_retrieval.max_results,
            )
        else:
            results = store.hybrid_search(
                query=search_query,
                embedder=doc_embedder,
                top_k=config.hybrid_retrieval.search_top_k,
            )

        if not results:
            return f"I couldn't find relevant information to answer: '{question}'. Please try rephrasing your question."

        # Step 3: Rerank results
        if analysis.needs_reranking and len(results) > config.hybrid_retrieval.rerank_top_k:
            try:
                results = reranker.rerank(
                    query=search_query,
                    results=results,
                    top_k=config.hybrid_retrieval.rerank_top_k,
                )
            except Exception as e:
                logger.warning(f"Reranking failed, using initial results: {e}")

        # Step 4: Synthesize complete answer
        try:
            synthesized_answer = synthesizer.synthesize(
                chunks=results,
                intent=analysis.intent,
                query=question,
            )
        except Exception as e:
            logger.warning(f"Synthesis failed, using concatenation: {e}")
            # Fallback to simple concatenation
            synthesized_answer = "\n\n".join([r.content for r in results[:config.hybrid_retrieval.max_results]])

        # Step 5: Format final answer with citations
        answer = f"**Answer to: {question}**\n\n"
        answer += synthesized_answer
        answer += "\n\n---\n\n"
        answer += "**Sources:**\n"
        
        # Add citations for each result
        seen_files = set()
        for result in results[:5]:  # Top 5 sources
            citation = format_citation(result.file_path, result.line_number)
            if result.file_path not in seen_files:
                answer += f"- {citation}\n"
                seen_files.add(result.file_path)

        elapsed = time.time() - start_time
        logger.info(f"✅ ask_tool completed in {elapsed:.2f}s: {len(results)} results, intent={analysis.intent.value}")
        logger.debug(f"Ask tool complete: {len(results)} results, intent={analysis.intent.value}")
        return answer

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ ask_tool failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return f"Error answering question: {str(e)}"

# MCP Tool definition
ask_tool_mcp = Tool(
    name="ask",
    description="Ask clarifications, comparisons, or explanations about the project. Returns synthesized answers from documentation.",
    inputSchema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Your question (e.g., 'Should I use aria-label or aria-labelledby?', 'What's the difference between v1 and v2 UI?')"
            },
            "context": {
                "type": "string",
                "description": "Optional context to help refine the answer",
                "default": ""
            }
        },
        "required": ["question"]
    }
)
