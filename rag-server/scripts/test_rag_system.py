#!/usr/bin/env python3
"""
RAG System Tests: Validate query intent, retrieval, reranking, synthesis.

Test categories:
- Query intent classification
- Hybrid retrieval accuracy
- Section-aware expansion
- Reranking effectiveness
- Answer synthesis for different intent types
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.core.query_analyzer import QueryAnalyzer, QueryIntent
from lib.core.embedding_manager import EmbeddingManager
from lib.core.reranker import Reranker
from lib.core.answer_synthesizer import AnswerSynthesizer
from lib.core.vector_store import SearchResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGSystemTests:
    """Test suite for RAG system components."""

    def __init__(self):
        """Initialize test components."""
        self.analyzer = QueryAnalyzer()
        self.embedder_mgr = EmbeddingManager(
            doc_model="sentence-transformers/all-MiniLM-L6-v2",
            code_model="microsoft/codebert-base"
        )
        self.reranker = Reranker()
        self.synthesizer = AnswerSynthesizer()

    def test_query_intent_classification(self):
        """Test query intent classification."""
        logger.info("🧪 Testing Query Intent Classification...")

        test_cases = [
            ("list all flows", QueryIntent.ENUMERATION),
            ("how many phases are there", QueryIntent.ENUMERATION),
            ("what is a flow", QueryIntent.EXPLANATION),
            ("explain the architecture", QueryIntent.EXPLANATION),
            ("what is the backend port", QueryIntent.EXPLANATION),  # "what is" = explanation
            ("show me the code for authentication", QueryIntent.CODE_SEARCH),
            ("find the login function", QueryIntent.CODE_SEARCH),
            ("difference between v1 and v2", QueryIntent.COMPARISON),
            ("compare phase 1 and phase 2", QueryIntent.COMPARISON),
        ]

        passed = 0
        failed = 0

        for query, expected_intent in test_cases:
            try:
                analysis = self.analyzer.analyze(query)
                if analysis.intent == expected_intent:
                    logger.info(f"  ✅ '{query}' → {analysis.intent.value}")
                    passed += 1
                else:
                    logger.warning(f"  ❌ '{query}' expected {expected_intent.value}, got {analysis.intent.value}")
                    failed += 1
            except Exception as e:
                logger.error(f"  ❌ Error analyzing '{query}': {e}")
                failed += 1

        logger.info(f"\n📊 Query Intent Classification: {passed} passed, {failed} failed\n")
        return passed, failed

    def test_embedding_models(self):
        """Test embedding models initialization."""
        logger.info("🧪 Testing Embedding Models...")

        try:
            # Test doc embedder
            doc_embedder = self.embedder_mgr.get_embedder("doc")
            doc_vector_size = self.embedder_mgr.get_vector_size("doc")
            logger.info(f"  ✅ Doc embedder loaded (vector size: {doc_vector_size})")

            # Test code embedder
            code_embedder = self.embedder_mgr.get_embedder("code")
            code_vector_size = self.embedder_mgr.get_vector_size("code")
            logger.info(f"  ✅ Code embedder loaded (vector size: {code_vector_size})")

            # Test embedding
            doc_text = "This is a test document about flows and phases."
            doc_embedding = self.embedder_mgr.embed_doc(doc_text)
            logger.info(f"  ✅ Doc embedding successful (shape: {len(doc_embedding)})")

            code_text = "def login_user(email, password): return authenticate(email, password)"
            code_embedding = self.embedder_mgr.embed_code(code_text)
            logger.info(f"  ✅ Code embedding successful (shape: {len(code_embedding)})")

            logger.info(f"\n📊 Embedding Models: All tests passed\n")
            return 2, 0

        except Exception as e:
            logger.error(f"  ❌ Embedding test failed: {e}")
            return 0, 2

    def test_reranking(self):
        """Test reranking functionality."""
        logger.info("🧪 Testing Reranking...")

        try:
            # Create mock search results
            mock_results = [
                SearchResult(
                    content="Flow 1 is about authentication and user login.",
                    file_path="flows/flow-1.md",
                    line_number=10,
                    score=0.8,
                    collection="local",
                    metadata={"section": "Overview"}
                ),
                SearchResult(
                    content="Flow 2 handles payment processing and transactions.",
                    file_path="flows/flow-2.md",
                    line_number=15,
                    score=0.75,
                    collection="local",
                    metadata={"section": "Overview"}
                ),
                SearchResult(
                    content="Authentication is implemented in multiple flows.",
                    file_path="docs/auth.md",
                    line_number=5,
                    score=0.70,
                    collection="local",
                    metadata={"section": "Authentication"}
                ),
            ]

            query = "how does authentication work"
            reranked = self.reranker.rerank(query, mock_results, top_k=2)

            if len(reranked) == 2:
                logger.info(f"  ✅ Reranking returned correct count (2)")
                logger.info(f"  ✅ Top result: {reranked[0].file_path}")
                logger.info(f"  ✅ Second result: {reranked[1].file_path}")
                logger.info(f"\n📊 Reranking: All tests passed\n")
                return 3, 0
            else:
                logger.error(f"  ❌ Expected 2 results, got {len(reranked)}")
                return 0, 1

        except Exception as e:
            logger.error(f"  ❌ Reranking test failed: {e}")
            return 0, 3

    def test_answer_synthesis(self):
        """Test answer synthesis for different intents."""
        logger.info("🧪 Testing Answer Synthesis...")

        passed = 0
        failed = 0

        # Test enumeration synthesis
        try:
            enum_results = [
                SearchResult(
                    content="1. Authentication flow\n2. Payment flow\n3. Notification flow",
                    file_path="flows.md",
                    line_number=1,
                    score=0.9,
                    collection="local",
                    metadata={"section": "Flows"}
                ),
            ]
            answer = self.synthesizer.synthesize(enum_results, QueryIntent.ENUMERATION)
            if "1." in answer and "2." in answer and "3." in answer:
                logger.info(f"  ✅ Enumeration synthesis successful")
                passed += 1
            else:
                logger.warning(f"  ❌ Enumeration synthesis incomplete")
                failed += 1
        except Exception as e:
            logger.error(f"  ❌ Enumeration synthesis failed: {e}")
            failed += 1

        # Test explanation synthesis
        try:
            expl_results = [
                SearchResult(
                    content="Flow-1 is the authentication flow.",
                    file_path="flows.md",
                    line_number=1,
                    score=0.9,
                    collection="local",
                    metadata={"section": "Flow-1"}
                ),
                SearchResult(
                    content="It handles user login and registration.",
                    file_path="flows.md",
                    line_number=5,
                    score=0.85,
                    collection="local",
                    metadata={"section": "Flow-1"}
                ),
            ]
            answer = self.synthesizer.synthesize(expl_results, QueryIntent.EXPLANATION)
            if "authentication" in answer.lower() and "login" in answer.lower():
                logger.info(f"  ✅ Explanation synthesis successful")
                passed += 1
            else:
                logger.warning(f"  ❌ Explanation synthesis incomplete")
                failed += 1
        except Exception as e:
            logger.error(f"  ❌ Explanation synthesis failed: {e}")
            failed += 1

        # Test code search synthesis
        try:
            code_results = [
                SearchResult(
                    content="def authenticate(email, password):\n    return validate_credentials(email, password)",
                    file_path="auth.py",
                    line_number=10,
                    score=0.95,
                    collection="local",
                    metadata={"section": "Auth", "content_type": "code"}
                ),
            ]
            answer = self.synthesizer.synthesize(code_results, QueryIntent.CODE_SEARCH)
            if "def authenticate" in answer or "auth.py" in answer:
                logger.info(f"  ✅ Code search synthesis successful")
                passed += 1
            else:
                logger.warning(f"  ❌ Code search synthesis incomplete")
                failed += 1
        except Exception as e:
            logger.error(f"  ❌ Code search synthesis failed: {e}")
            failed += 1

        logger.info(f"\n📊 Answer Synthesis: {passed} passed, {failed} failed\n")
        return passed, failed

    def run_all_tests(self):
        """Run all test suites."""
        logger.info("=" * 60)
        logger.info("🚀 RAG System Test Suite")
        logger.info("=" * 60 + "\n")

        total_passed = 0
        total_failed = 0

        # Run tests
        p, f = self.test_query_intent_classification()
        total_passed += p
        total_failed += f

        p, f = self.test_embedding_models()
        total_passed += p
        total_failed += f

        p, f = self.test_reranking()
        total_passed += p
        total_failed += f

        p, f = self.test_answer_synthesis()
        total_passed += p
        total_failed += f

        # Summary
        logger.info("=" * 60)
        logger.info("📊 Test Summary")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {total_passed}")
        logger.info(f"❌ Failed: {total_failed}")
        logger.info(f"📈 Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
        logger.info("=" * 60 + "\n")

        return total_failed == 0


def main():
    """Run RAG system tests."""
    try:
        tester = RAGSystemTests()
        success = tester.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

