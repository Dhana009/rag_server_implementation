#!/usr/bin/env python3
"""Verify RAG system setup"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("✅ Checking RAG System Components...\n")

components = {
    "config": "Config management",
    "core.embedding_manager": "Dual embeddings",
    "core.query_analyzer": "Intent classification",
    "core.vector_store": "Hybrid search",
    "core.reranker": "Cross-encoder reranking",
    "core.answer_synthesizer": "Answer generation",
    "indexing.indexer": "Doc indexing",
    "indexing.code_parser": "Code parsing",
    "indexing.code_chunker": "Code chunking",
    "indexing.code_indexer": "Code indexing",
}

failed = []
for module, desc in components.items():
    try:
        __import__(module)
        print(f"  ✅ {module:20} - {desc}")
    except ImportError as e:
        print(f"  ❌ {module:20} - {desc} ({str(e)[:50]})")
        failed.append(module)

print()
if failed:
    print(f"❌ {len(failed)} components failed to import")
    sys.exit(1)
else:
    print("✅ All components ready!")
    sys.exit(0)

