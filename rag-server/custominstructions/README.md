# Custom Instructions - Test Data

This folder contains test files for validating the RAG server functionality. These files are used to verify that indexing, search, and question-answering work correctly.

## Test Files

### `test-doc.md`
A simple markdown document containing:
- Test documentation structure
- Features list
- Configuration details
- Testing purposes

**Purpose**: Test document indexing and retrieval

### `test-code.py`
A simple Python file containing:
- Test functions
- Test class with methods
- Main function

**Purpose**: Test code indexing and retrieval

## How to Test

### For AI Assistants

Follow these steps to test the RAG server:

#### Step 1: Ensure Test Files Are Indexed

The test files should be included in `mcp-config.json`:

```json
{
  "cloud_docs": [
    "rag-server/README.md",
    "rag-server/custominstructions/**/*.md"
  ],
  "code_paths": [
    "rag-server/**/*.py",
    "rag-server/custominstructions/**/*.py"
  ]
}
```

#### Step 2: Index the Test Data

```bash
cd rag-server
python rag_cli.py index
```

**Expected Output:**
- `test-doc.md` should be indexed (4 chunks)
- `test-code.py` should be indexed (3 chunks)
- No errors

#### Step 3: Test Search Tool

Test document search:
```python
# Via MCP
search(query="test document features search functionality", top_k=3)
```

**Expected**: Should find results from `test-doc.md`

Test code search:
```python
# Via MCP
search(query="TestClass greet function", top_k=2, content_type="code")
```

**Expected**: Should find results from `test-code.py`

#### Step 4: Test Ask Tool

```python
# Via MCP
ask(question="What is the TestClass in the test code?")
```

**Expected**: Should return information about the TestClass from `test-code.py`

#### Step 5: Test Explain Tool

```python
# Via MCP
explain(topic="test documentation configuration")
```

**Expected**: Should provide explanation about test documentation

#### Step 6: Verify Stats

```bash
python rag_cli.py stats
```

**Expected**: Should show test files in collection statistics

#### Step 7: Clean Up Test Data (Optional)

To remove test data from the database:

1. Remove test files from `mcp-config.json`
2. Run cleanup:
   ```bash
   python rag_cli.py index --cleanup
   ```
3. This will soft-delete chunks from deleted files

## Test Checklist

- [ ] Test files exist in `custominstructions/` folder
- [ ] Test files are included in `mcp-config.json`
- [ ] Indexing completes without errors
- [ ] Search tool finds test documents
- [ ] Search tool finds test code
- [ ] Ask tool answers questions about test data
- [ ] Explain tool provides explanations
- [ ] Stats command shows test data
- [ ] Cleanup removes test data when files are deleted

## What Each Test Validates

### Document Indexing Test
- ✅ Markdown files are parsed correctly
- ✅ Chunks are created properly
- ✅ Metadata is stored correctly

### Code Indexing Test
- ✅ Python files are parsed correctly
- ✅ Functions and classes are extracted
- ✅ Code chunks are indexed

### Search Test
- ✅ Semantic search works
- ✅ Results are relevant
- ✅ Content type filtering works

### Ask Test
- ✅ Query intent classification works
- ✅ RAG pipeline retrieves relevant chunks
- ✅ Answer synthesis works

### Explain Test
- ✅ Topic explanation works
- ✅ Context is retrieved correctly
- ✅ Comprehensive explanations are generated

## Troubleshooting

**Test files not found during indexing:**
- Check `mcp-config.json` includes the paths
- Verify files exist in `custominstructions/` folder
- Check file permissions

**Search returns no results:**
- Verify indexing completed successfully
- Check collection stats: `python rag_cli.py stats`
- Ensure test files were actually indexed

**Cleanup doesn't remove test data:**
- Test files must be removed from `mcp-config.json` first
- Run `python rag_cli.py index --cleanup`
- Check stats to verify chunks are soft-deleted

## Notes

- Test files are intentionally small for fast testing
- These files can be safely deleted and recreated
- The test data is isolated in the `custominstructions/` folder
- Always clean up test data after testing to keep the database clean

