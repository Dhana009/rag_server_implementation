# AI Testing Instructions - RAG Server

**For AI Assistants**: This document provides clear, step-by-step instructions for testing the RAG server.

## Quick Start

1. **Test files are ready** in `rag-server/custominstructions/`
2. **Config is set up** - test files are included in `mcp-config.json`
3. **Just run the tests** - follow the steps below

## Complete Test Procedure

### Step 1: Index Test Data

```bash
cd rag-server
python rag_cli.py index
```

**What to expect**:
- ✅ `test-doc.md` indexed (4 chunks)
- ✅ `test-code.py` indexed (3 chunks)
- ✅ Total: ~7 chunks from test files
- ✅ No errors

**Time**: ~30-60 seconds (first time may be slower due to model downloads)

### Step 2: Verify Indexing

```bash
python rag_cli.py stats
```

**What to expect**:
- Shows collection statistics
- Cloud and local collections should have matching counts
- Should include chunks from test files

### Step 3: Test MCP Tools

#### Test 3a: Search Tool

**Document Search**:
```python
# Use MCP search tool
search(query="test document features search functionality", top_k=3)
```

**Expected**:
- ✅ Finds content from `test-doc.md`
- ✅ Mentions "Search Functionality", "Question Answering", "Code Indexing"
- ✅ Score > 0.4

**Code Search**:
```python
# Use MCP search tool
search(query="TestClass greet function", top_k=2, content_type="code")
```

**Expected**:
- ✅ Finds content from `test-code.py`
- ✅ Mentions `TestClass` and `greet()` method
- ✅ Shows code snippets

#### Test 3b: Ask Tool

**Question 1**:
```python
# Use MCP ask tool
ask(question="What is the TestClass in the test code?")
```

**Expected**:
- ✅ Explains TestClass structure
- ✅ Mentions `__init__` and `greet()` methods
- ✅ References `test-code.py`

**Question 2**:
```python
# Use MCP ask tool
ask(question="What features does the test document mention?")
```

**Expected**:
- ✅ Lists 3 features from `test-doc.md`
- ✅ Formatted as numbered list
- ✅ References test document

#### Test 3c: Explain Tool

```python
# Use MCP explain tool
explain(topic="test documentation configuration")
```

**Expected**:
- ✅ Comprehensive explanation
- ✅ References `test-doc.md` content
- ✅ Explains configuration details

### Step 4: Verify All Tests Passed

**Success Criteria**:
- ✅ All indexing completed without errors
- ✅ Search finds test file content
- ✅ Ask tool provides accurate answers
- ✅ Explain tool provides comprehensive explanations
- ✅ Stats show test file chunks

## Test File Details

### `test-doc.md`
- **Location**: `rag-server/custominstructions/test-doc.md`
- **Content**: Test documentation with features, configuration, and testing info
- **Chunks**: ~4 chunks when indexed
- **Purpose**: Test document indexing and retrieval

### `test-code.py`
- **Location**: `rag-server/custominstructions/test-code.py`
- **Content**: Python file with `test_function()`, `TestClass`, and `main()`
- **Chunks**: ~3 chunks when indexed
- **Purpose**: Test code indexing and retrieval

## Configuration

Test files are automatically included via `mcp-config.json`:

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

## Troubleshooting

**Test files not indexed?**
- Check `mcp-config.json` includes the paths above
- Verify files exist: `ls rag-server/custominstructions/`
- Re-run indexing: `python rag_cli.py index`

**Search returns no results?**
- Verify indexing: `python rag_cli.py stats`
- Check test files were indexed (chunk count should include test files)
- Re-index if needed: `python rag_cli.py index`

**Unexpected results?**
- Re-index: `python rag_cli.py index`
- Check logs: `rag-server/rag-server.log`
- Verify test file content matches expected

## Cleanup (After Testing)

To remove test data from database:

1. **Remove from config** (temporarily):
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

3. **Restore config** to keep test files for future use

## Summary

**Test Files**: `test-doc.md` and `test-code.py` in `custominstructions/` folder
**Config**: Already set up in `mcp-config.json`
**Testing**: Index → Verify → Test Tools → Verify Results
**Cleanup**: Optional - remove from config and run cleanup

**All tests should complete in < 2 minutes** (excluding first-time model downloads).

