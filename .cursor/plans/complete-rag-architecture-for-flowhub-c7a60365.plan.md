<!-- c7a60365-6d93-448c-a2c5-3e6536c6b2b0 b1facdbf-3425-419d-ad6f-3b4eae5ee00d -->
# Production-Ready RAG Implementation Plan

## Core Principles

1. **No Shortcuts**: Implement best practices from day one
2. **Separate Embeddings**: Code-specific (CodeBERT) for code, text embeddings (MiniLM) for docs
3. **Production-Ready**: All advanced features (hybrid retrieval, reranking, synthesis)
4. **Scalable**: Designed for known project scale (entire codebase + all docs)
5. **Industry Standards**: Follow researched best practices, even if complex

---

## Architecture Overview

```
User Query
    ↓
Query Intent Classifier
    ↓
Hybrid Retrieval (BM25 + Vector Search)
    ├─ Text Embeddings (MiniLM) for docs
    └─ Code Embeddings (CodeBERT) for code
    ↓
Section-Aware Expansion (Qdrant filters)
    ↓
Reranking (Cross-encoder model)
    ↓
Answer Synthesis (merge, deduplicate, preserve structure)
    ↓
Complete Answer
```

---

## Phase 0: Quality Framework Setup (BEFORE Implementation)

**Purpose**: Establish quality standards, checklists, and testing framework before starting implementation

**Time Estimate**: 2-3 hours

### 0.1 Quality Checklist Template

**File**: `LinkedIn/mcp-server/QUALITY_CHECKLIST.md` (NEW)

**Content**:

- Core principles checklist (per component)
- Error handling requirements
- Edge cases to consider
- Regression prevention checklist
- Code review checklist

### 0.2 Error Handling Standards

**File**: `LinkedIn/mcp-server/ERROR_HANDLING.md` (NEW)

**Standards**:

- All API calls must have try/except blocks
- All model loading must handle failures gracefully
- All file operations must handle missing files
- All parsing must handle malformed input
- All retrieval must handle empty results
- Logging for all errors with context

### 0.3 Test Templates

**File**: `LinkedIn/mcp-server/test_templates.py` (NEW)

**Templates**:

- Unit test template
- Integration test template
- Edge case test template
- Error scenario test template
- Performance test template

### 0.4 Design Decision Log

**File**: `LinkedIn/mcp-server/DESIGN_DECISIONS.md` (NEW)

**Template for each decision**:

- Date
- Component
- Decision
- Rationale
- Alternatives considered
- Trade-offs

### 0.5 Edge Cases Documentation

**File**: `LinkedIn/mcp-server/EDGE_CASES.md` (NEW)

**Document all edge cases**:

- Query processing edge cases
- Retrieval edge cases
- Synthesis edge cases
- Code parsing edge cases
- Integration edge cases

### 0.6 Logging & Monitoring Setup

**Enhancements**:

- Structured logging format
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Performance logging (query time, retrieval time)
- Error tracking

**Key Requirements**:

- Log all major operations
- Log errors with full context
- Log performance metrics
- Make logs searchable

### 0.7 Component Quality Checklist

**For each component, verify**:

- [ ] Meets core purpose (Python handles processing, AI receives clean answer)
- [ ] Aligns with architecture
- [ ] Handles all error scenarios
- [ ] Handles all edge cases
- [ ] Has unit tests
- [ ] Has integration tests
- [ ] Is documented
- [ ] No regressions introduced
- [ ] Performance acceptable
- [ ] Code is maintainable

---

## Phase 1: Core Infrastructure Setup

### 1.1 Enhanced Configuration System

**File**: `LinkedIn/mcp-server/config.py`

**Changes**:

- Add separate embedding model configs (doc_embedding_model, code_embedding_model)
- Add reranking model config
- Add hybrid retrieval weights
- Add code indexing paths and settings
- Add metadata schema definitions

**Configuration Structure**:

```python
class Config:
    # Existing fields...
    doc_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    code_embedding_model: str = "microsoft/codebert-base"  # Code-specific
    reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Hybrid retrieval
    hybrid_weights: Dict[str, float] = {"bm25": 0.3, "vector": 0.7}
    search_top_k: int = 20
    rerank_top_k: int = 10
    max_results: int = 25
    
    # Code indexing
    code_paths: List[str]
    code_chunk_strategy: str = "function_level"
    
    # Enhanced metadata
    metadata_schema: Dict  # content_type, language, etc.
```

### 1.2 Dual Embedding System

**File**: `LinkedIn/mcp-server/embedding_manager.py` (NEW)

**Purpose**: Manage separate embedding models for code and docs

**Implementation**:

- Load text embedding model (MiniLM) for documents
- Load code embedding model (CodeBERT) for code
- Route embeddings based on content_type
- Handle model initialization and caching

**Key Methods**:

- `get_embedder(content_type: str) -> SentenceTransformer`
- `embed_doc(content: str) -> List[float]`
- `embed_code(content: str) -> List[float]`

---

## Phase 2: Query Processing Pipeline

### 2.1 Query Intent Classifier

**File**: `LinkedIn/mcp-server/query_analyzer.py` (NEW)

**Purpose**: Classify query intent to optimize retrieval strategy

**Query Types**:

- `ENUMERATION`: "list all X", "how many Y" → Need complete sets
- `EXPLANATION`: "what is X", "how does Y work" → Need coherent explanations
- `CODE_SEARCH`: "show me code", "find function" → Need code chunks
- `COMPARISON`: "difference between A and B" → Need both sides
- `FACTUAL`: "what is the value of X" → Need exact answer

**Implementation**:

- Pattern matching for keywords
- ML-based classification (optional future enhancement)
- Returns intent + optimized retrieval parameters

### 2.2 Hybrid Retrieval System

**File**: `LinkedIn/mcp-server/vector_store.py` (ENHANCE)

**New Methods**:

- `hybrid_search()`: BM25 + Vector search with weighted combination
- `search_with_expansion()`: Section-aware retrieval with filters
- `get_all_chunks_from_section()`: Efficient section retrieval using Qdrant filters

**Implementation Details**:

- Use Qdrant's native BM25 support
- Combine BM25 scores (0.3) + Vector scores (0.7)
- Route to appropriate embedder based on content_type
- Use metadata filters for section-aware expansion

### 2.3 Reranking System

**File**: `LinkedIn/mcp-server/reranker.py` (NEW)

**Purpose**: Rerank initial results using cross-encoder model

**Implementation**:

- Load `cross-encoder/ms-marco-MiniLM-L-6-v2` model
- Rerank top 20 results from hybrid search
- Return top 10 reranked results
- Cache model to avoid reloading

**Key Methods**:

- `rerank(query: str, results: List[SearchResult]) -> List[SearchResult]`

---

## Phase 3: Document Indexing Enhancement

### 3.1 Enhanced Markdown Chunking

**File**: `LinkedIn/mcp-server/indexer.py` (ENHANCE)

**Enhancements**:

- Preserve numbered lists (detect and keep together, even if > 1000 chars)
- Preserve tables (detect markdown tables, keep together)
- Preserve code blocks (keep together)
- Add content_type metadata ("list", "table", "text", "code")
- Add list_length metadata for numbered lists
- Add is_complete flag for structured content

**Chunking Strategy**:

- Chunk by sections (## headers) - PRIMARY
- If section contains numbered list → keep entire list in one chunk
- If section contains table → keep entire table in one chunk
- Fallback to size-based splitting only if no structure detected

### 3.2 Document Indexing Pipeline

**File**: `LinkedIn/mcp-server/indexer.py` (ENHANCE)

**Changes**:

- Use doc embedding model (MiniLM) for all document chunks
- Add content_type to metadata
- Enhanced metadata structure

---

## Phase 4: Code Indexing System

### 4.1 Code Parser (Tree-sitter)

**File**: `LinkedIn/mcp-server/code_parser.py` (NEW)

**Purpose**: Parse code files using AST (Tree-sitter)

**Supported Languages**:

- TypeScript/JavaScript (tree-sitter-typescript)
- Python (tree-sitter-python)

**Implementation**:

- Initialize Tree-sitter parsers for each language
- Parse file to AST
- Extract functions, classes, methods
- Preserve class context (include class name in function chunks)
- Extract metadata: function name, class name, line numbers, docstrings, imports

**Key Methods**:

- `parse_typescript(file_path: str, content: str) -> List[CodeChunk]`
- `parse_python(file_path: str, content: str) -> List[CodeChunk]`
- `extract_functions(node, class_context: str) -> List[FunctionInfo]`

### 4.2 Code Chunker

**File**: `LinkedIn/mcp-server/code_chunker.py` (NEW)

**Purpose**: Create function-level chunks from parsed code

**Strategy**:

- Each function = 1 chunk
- Include class context in chunk (if function is in class)
- Include imports at top of chunk
- Include docstring if present
- Preserve function signature

**Chunk Structure**:

```python
{
    "content": "imports + class context + function signature + function body",
    "line_start": int,
    "line_end": int,
    "metadata": {
        "content_type": "code",
        "language": "typescript" | "python",
        "function_name": str,
        "class_name": str | None,
        "file_path": str,
        "imports": List[str],
        "docstring": str | None
    }
}
```

### 4.3 Code Indexing Pipeline

**File**: `LinkedIn/mcp-server/code_indexer.py` (NEW)

**Purpose**: Index code files into vector database

**Process**:

1. Detect file type (TypeScript, Python, etc.)
2. Parse file using code_parser
3. Create chunks using code_chunker
4. Embed using code embedding model (CodeBERT)
5. Index into vector store with metadata

**Key Methods**:

- `index_code_file(file_path: str, collection: str) -> bool`
- `index_all_code_files(config: Config) -> Dict[str, int]`

---

## Phase 5: Answer Synthesis

### 5.1 Answer Synthesizer

**File**: `LinkedIn/mcp-server/answer_synthesizer.py` (NEW)

**Purpose**: Synthesize complete answers from retrieved chunks

**Strategies by Query Intent**:

**Enumeration Queries**:

- Extract all numbered items from chunks
- Sort by number
- Deduplicate
- Verify completeness (e.g., 1-18 for flows)
- Format as complete numbered list

**Explanation Queries**:

- Merge related chunks from same section/file
- Order by line numbers (maintain document order)
- Remove overlaps
- Format as coherent explanation

**Code Search Queries**:

- Group by file
- Preserve code formatting
- Include file path and line numbers
- Format as code blocks

**Comparison Queries**:

- Separate chunks by topic (A vs B)
- Format side-by-side or sequential

**Key Methods**:

- `synthesize(chunks: List[SearchResult], intent: QueryIntent) -> str`
- `_synthesize_enumeration(chunks: List[SearchResult]) -> str`
- `_synthesize_explanation(chunks: List[SearchResult]) -> str`
- `_synthesize_code_search(chunks: List[SearchResult]) -> str`

---

## Phase 6: Integration & Tools

### 6.1 Enhanced Ask Tool

**File**: `LinkedIn/mcp-server/tools/ask.py` (REWRITE)

**New Pipeline**:

1. Classify query intent
2. Hybrid retrieval (BM25 + Vector, route to correct embedder)
3. Section-aware expansion (if applicable)
4. Reranking
5. Answer synthesis
6. Return complete answer

**Changes**:

- Remove truncation (return full content)
- Use new retrieval pipeline
- Use answer synthesizer
- Support all query types

### 6.2 Enhanced Search Tool

**File**: `LinkedIn/mcp-server/tools/search.py` (ENHANCE)

**Enhancements**:

- Support content_type filtering (doc, code, config, test)
- Support language filtering (typescript, python, markdown)
- Show more content (500 chars instead of 200)
- Better formatting

### 6.3 Code Search Tool (NEW)

**File**: `LinkedIn/mcp-server/tools/code_search.py` (NEW)

**Purpose**: Specialized tool for code search

**Features**:

- Search only code chunks
- Filter by language, file_path, function_name
- Return formatted code with context

---

## Phase 7: Indexing Scripts

### 7.1 Enhanced Index All Script

**File**: `LinkedIn/mcp-server/index_all.py` (ENHANCE)

**Changes**:

- Index documents (using enhanced chunking)
- Index code files (using code parser)
- Support incremental updates
- Show progress and stats

### 7.2 Code Indexing Script

**File**: `LinkedIn/mcp-server/index_code.py` (NEW)

**Purpose**: Index only code files (for incremental updates)

**Features**:

- Index all code files from config
- Support single file indexing
- Incremental updates (only changed files)

---

## Phase 8: Configuration Updates

### 8.1 Enhanced Config File

**File**: `LinkedIn/mcp-config.json` (UPDATE)

**New Structure**:

```json
{
  "cloud_qdrant": {...},
  "local_qdrant": {...},
  
  "embedding_models": {
    "doc": "sentence-transformers/all-MiniLM-L6-v2",
    "code": "microsoft/codebert-base",
    "reranking": "cross-encoder/ms-marco-MiniLM-L-6-v2"
  },
  
  "retrieval": {
    "search_top_k": 20,
    "rerank_top_k": 10,
    "max_results": 25,
    "hybrid_weights": {
      "bm25": 0.3,
      "vector": 0.7
    }
  },
  
  "chunking": {
    "doc_chunk_size": 1000,
    "doc_chunk_overlap": 100,
    "code_chunk_strategy": "function_level",
    "code_chunk_overlap": 50
  },
  
  "doc_paths": [...],
  "code_paths": [
    "flowhub_reset_design/backend/**/*.{ts,js,json}",
    "flowhub_reset_design/frontend/**/*.{ts,tsx,js,jsx,json}",
    "LinkedIn/mcp-server/**/*.py",
    "tests/**/*.{ts,js,py}"
  ],
  "exclude_patterns": [...]
}
```

---

## Phase 9: Dependencies

### 9.1 Requirements Update

**File**: `LinkedIn/mcp-server/requirements.txt` (UPDATE)

**New Dependencies**:

```
# Code parsing
tree-sitter==0.20.4
tree-sitter-typescript==0.20.3
tree-sitter-python==0.20.4

# Code embeddings (CodeBERT)
transformers>=4.30.0
torch>=2.0.0

# Reranking
sentence-transformers>=2.2.0  # Already have, ensure version supports cross-encoders
```

---

## Phase 10: Testing & Validation

### 10.1 Test Suite

**File**: `LinkedIn/mcp-server/test_rag_system.py` (NEW)

**Test Cases**:

1. Enumeration query: "List all 18 flows" → Complete list
2. Explanation query: "What is the selector policy?" → Coherent explanation
3. Code search: "Show me login authentication code" → Relevant code chunks
4. Cross-domain: "What's the architecture for flow-4?" → Docs + code
5. Comparison: "Difference between v1 and v2 UI" → Both sides

**Performance Tests**:

- Query response time < 1 second
- Retrieval accuracy (precision@10, recall@10)
- Answer completeness

---

## Implementation Order

0. **Phase 0**: Quality Framework Setup (BEFORE implementation starts)
1. **Phase 1**: Core Infrastructure (config, embedding manager)
2. **Phase 2**: Query Processing (intent classifier, hybrid retrieval, reranking)
3. **Phase 3**: Document Indexing Enhancement
4. **Phase 4**: Code Indexing System
5. **Phase 5**: Answer Synthesis
6. **Phase 6**: Integration & Tools
7. **Phase 7**: Indexing Scripts
8. **Phase 8**: Configuration Updates
9. **Phase 9**: Dependencies
10. **Phase 10**: Testing & Validation
11. **Phase 11**: Quality Assurance & Validation (AFTER implementation)

---

## Key Design Decisions

1. **Separate Embeddings**: CodeBERT for code, MiniLM for docs (best accuracy)
2. **Function-Level Code Chunking**: Optimal for code search
3. **Unified Collection**: Better for cross-domain queries, use metadata filtering
4. **Hybrid Retrieval**: BM25 + Vector (best recall and precision)
5. **Reranking**: Cross-encoder model (significant accuracy improvement)
6. **Section-Aware Expansion**: Complete answers for enumeration queries
7. **Answer Synthesis**: Reconstruct complete structures (lists, tables, code)

---

## Success Criteria

1. ✅ Enumeration queries return complete lists (e.g., all 18 flows)
2. ✅ Code search finds relevant functions with context
3. ✅ Cross-domain queries work (docs + code)
4. ✅ Response time < 1 second
5. ✅ Answer completeness: 100% for enumeration, coherent for explanation
6. ✅ Scalable to entire codebase + all docs

---

## Estimated Implementation Time

- Phase 1: 2-3 hours
- Phase 2: 4-5 hours
- Phase 3: 2-3 hours
- Phase 4: 5-6 hours
- Phase 5: 3-4 hours
- Phase 6: 2-3 hours
- Phase 7: 1-2 hours
- Phase 8: 1 hour
- Phase 9: 1 hour
- Phase 10: 2-3 hours

**Total: 23-31 hours**

---

**Status**: Plan Ready for Review

**Approach**: Production-ready from day one, no shortcuts

**Next Step**: Review and approve plan before implementation

### To-dos

- [ ] Enhance config.py with separate embedding models (doc/code), reranking model, hybrid retrieval settings, code indexing paths
- [ ] Create embedding_manager.py to manage separate embedding models (MiniLM for docs, CodeBERT for code)
- [ ] Create query_analyzer.py to classify query intent (enumeration, explanation, code_search, comparison, factual)
- [ ] Enhance vector_store.py with hybrid_search() (BM25 + Vector), search_with_expansion() (section-aware), get_all_chunks_from_section() (Qdrant filters)
- [ ] Create reranker.py with cross-encoder model (ms-marco-MiniLM-L-6-v2) to rerank top 20 results to top 10
- [ ] Enhance indexer.py chunk_markdown() to preserve numbered lists, tables, code blocks; add content_type metadata, list_length, is_complete flags
- [ ] Create code_parser.py using Tree-sitter to parse TypeScript and Python files, extract functions, classes, methods with metadata
- [ ] Create code_chunker.py for function-level chunking, preserve class context, include imports and docstrings
- [ ] Create code_indexer.py to index code files using code parser, chunker, and code embedding model (CodeBERT)
- [ ] Create answer_synthesizer.py with strategies for enumeration (reconstruct lists), explanation (merge chunks), code_search (format code), comparison (side-by-side)
- [ ] Rewrite tools/ask.py to use new pipeline: intent classification → hybrid retrieval → section-aware expansion → reranking → answer synthesis
- [ ] Enhance tools/search.py with content_type/language filtering, show 500 chars instead of 200, better formatting
- [ ] Create tools/code_search.py specialized tool for code search with language/file_path/function_name filtering
- [ ] Enhance index_all.py to index both documents (enhanced chunking) and code files (code parser), support incremental updates
- [ ] Create index_code.py script for code-only indexing, support single file and incremental updates
- [ ] Update mcp-config.json with new structure: embedding_models, retrieval settings, chunking settings, code_paths
- [ ] Update requirements.txt with tree-sitter, tree-sitter-typescript, tree-sitter-python, transformers, torch for CodeBERT
- [ ] Create test_rag_system.py with test cases for enumeration, explanation, code_search, cross-domain queries, performance tests