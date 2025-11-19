# RAG Server Testing Guide

**For AI Assistants**: This guide explains how to test the RAG server using the test files in this folder.

## Overview

The `custominstructions/` folder contains test files specifically designed for validating RAG server functionality. These files are:
- **Small and fast** - Quick to index and test
- **Well-structured** - Easy to verify results
- **Isolated** - Can be safely added/removed without affecting production data

## Test Files

### 1. `test-doc.md`
**Purpose**: Test document indexing and retrieval

**Content**:
- Test documentation structure
- Features list (numbered items)
- Configuration details
- Testing purposes

**What it tests**:
- Markdown parsing
- Document chunking
- Semantic search for docs
- Question answering about documentation

### 2. `test-code.py`
**Purpose**: Test code indexing and retrieval

**Content**:
- `test_function()` - Simple function
- `TestClass` - Class with `__init__` and `greet()` methods
- `main()` - Main function

**What it tests**:
- Python code parsing
- Function/class extraction
- Code chunking
- Semantic search for code

## Complete Testing Workflow

### Step 1: Verify Configuration

Check that `mcp-config.json` includes test files:

```json
{
  "cloud_docs": [
    "rag-server/README.md",
    "rag-server/custominstructions/**/*.md"  // ← Test docs
  ],
  "code_paths": [
    "rag-server/**/*.py",
    "rag-server/custominstructions/**/*.py"  // ← Test code
  ]
}
```

### Step 2: Index Test Data

```bash
cd rag-server
python rag_cli.py index
```

**Expected Results**:
- ✅ `test-doc.md` indexed (4 chunks)
- ✅ `test-code.py` indexed (3 chunks)
- ✅ No errors
- ✅ Total: ~7 chunks from test files

### Step 3: Verify Indexing

```bash
python rag_cli.py stats
```

**Expected**: Should show test files in collection statistics

### Step 4: Test Search Tool

**Test 1: Document Search**
```python
# Via MCP search tool
search(query="test document features search functionality", top_k=3)
```

**Expected Results**:
- Should find `test-doc.md` content
- Should mention "Search Functionality", "Question Answering", "Code Indexing"
- Score should be > 0.4

**Test 2: Code Search**
```python
# Via MCP search tool
search(query="TestClass greet function", top_k=2, content_type="code")
```

**Expected Results**:
- Should find `test-code.py` content
- Should mention `TestClass` and `greet()` method
- Should show code snippets

### Step 5: Test Ask Tool

**Test 1: Question about Test Class**
```python
# Via MCP ask tool
ask(question="What is the TestClass in the test code?")
```

**Expected Results**:
- Should explain TestClass from `test-code.py`
- Should mention `__init__` and `greet()` methods
- Should reference the test file

**Test 2: Question about Features**
```python
# Via MCP ask tool
ask(question="What features does the test document mention?")
```

**Expected Results**:
- Should list the 3 features from `test-doc.md`
- Should be formatted as a numbered list
- Should reference the test document

### Step 6: Test Explain Tool

```python
# Via MCP explain tool
explain(topic="test documentation configuration")
```

**Expected Results**:
- Should provide comprehensive explanation
- Should reference test-doc.md content
- Should explain configuration details

### Step 7: Test Stats Command

```bash
python rag_cli.py stats
```

**Expected Results**:
- Should show total chunks including test files
- Cloud and local collections should match
- Should show ~7+ chunks from test files

### Step 8: Test Cleanup (Optional)

To test cleanup functionality:

1. **Temporarily remove test files from config**:
   ```json
   {
     "cloud_docs": ["rag-server/README.md"],  // Remove test path
     "code_paths": ["rag-server/**/*.py"]     // Remove test path
   }
   ```

2. **Run cleanup**:
   ```bash
   python rag_cli.py index --cleanup
   ```

3. **Expected**: Test file chunks should be soft-deleted

4. **Restore config** to re-enable test files

## Test Validation Checklist

Use this checklist to verify all functionality:

### Indexing Tests
- [ ] Test files are found during indexing
- [ ] `test-doc.md` creates ~4 chunks
- [ ] `test-code.py` creates ~3 chunks
- [ ] No indexing errors
- [ ] Stats show test file chunks

### Search Tests
- [ ] Document search finds `test-doc.md` content
- [ ] Code search finds `test-code.py` content
- [ ] Results are relevant (score > 0.3)
- [ ] Content type filtering works
- [ ] Top-k parameter works

### Ask Tool Tests
- [ ] Questions about test class return correct answers
- [ ] Questions about features return numbered lists
- [ ] Answers reference test files
- [ ] Query intent classification works
- [ ] Reranking improves results

### Explain Tool Tests
- [ ] Explanations are comprehensive
- [ ] Test file content is included
- [ ] Context is relevant
- [ ] Multiple sources are cited

### Cleanup Tests
- [ ] Soft-delete works when files removed from config
- [ ] Chunks are marked as deleted (not removed)
- [ ] Stats reflect deleted chunks
- [ ] Recovery is possible

## Quick Test Commands

**Full test suite** (for AI assistants):
```bash
# 1. Index
cd rag-server && python rag_cli.py index

# 2. Check stats
python rag_cli.py stats

# 3. Test via MCP tools (use search, ask, explain)
# 4. Verify results match expected outcomes
```

## Troubleshooting

**Problem**: Test files not indexed
- **Solution**: Check `mcp-config.json` includes `rag-server/custominstructions/**/*.md` and `rag-server/custominstructions/**/*.py`
- **Verify**: Files exist in `custominstructions/` folder

**Problem**: Search returns no results
- **Solution**: Verify indexing completed: `python rag_cli.py stats`
- **Check**: Test files were actually indexed (should see chunks count increase)

**Problem**: Results don't match expected
- **Solution**: Re-index: `python rag_cli.py index`
- **Note**: First-time indexing may take longer (models download)

## Notes for AI Assistants

1. **Always verify indexing first** - Run `python rag_cli.py stats` before testing
2. **Test files are small** - Results should be fast (< 5 seconds per query)
3. **Isolated testing** - Test files don't affect production data
4. **Clean up after** - Remove test paths from config and run cleanup when done
5. **Reusable** - Test files can be deleted and recreated anytime

## Expected Test Results Summary

| Test | Expected Result | Validation |
|------|----------------|------------|
| Index test-doc.md | 4 chunks created | Check stats |
| Index test-code.py | 3 chunks created | Check stats |
| Search "test document" | Finds test-doc.md | Score > 0.4 |
| Search "TestClass" | Finds test-code.py | Score > 0.3 |
| Ask "What is TestClass?" | Explains class structure | References test-code.py |
| Ask "What features?" | Lists 3 features | Numbered list format |
| Explain "test documentation" | Comprehensive explanation | Multiple sources |

## Success Criteria

All tests pass if:
- ✅ All indexing completes without errors
- ✅ Search finds relevant results from test files
- ✅ Ask tool provides accurate answers
- ✅ Explain tool provides comprehensive explanations
- ✅ Stats reflect test file chunks
- ✅ Cleanup works correctly

If all criteria are met, the RAG server is working correctly!

