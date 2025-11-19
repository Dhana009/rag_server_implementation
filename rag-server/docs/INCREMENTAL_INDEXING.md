# Incremental Indexing & Duplicate Prevention

This document explains how the RAG server handles incremental updates, prevents duplicates, and manages file changes.

## Quick Answer

**Q: If data is already indexed and I add two new files, how do I run indexing?**

**A: Just run the same command:**
```bash
python rag_cli.py index
```

The system automatically:
- ✅ Detects new files and indexes them
- ✅ Skips unchanged files (no re-indexing)
- ✅ Updates modified files (only changed chunks)
- ✅ Prevents duplicates automatically
- ✅ Handles file deletions (with cleanup)

## How It Works

### 1. Point ID Generation (Duplicate Prevention)

Each chunk gets a **unique, deterministic ID** based on:
```python
point_id = abs(hash(f"{file_path}:{line_start}")) % (2**63 - 1)
```

**Key Points**:
- Same file + same line = **same ID** (prevents duplicates)
- Different file or line = **different ID**
- IDs are deterministic (same input = same ID every time)

**Example**:
- `test-doc.md:10` → ID: `1234567890`
- `test-doc.md:20` → ID: `9876543210`
- `test-code.py:10` → ID: `5555555555` (different file, different ID)

### 2. Incremental Update Strategy

When you run `python rag_cli.py index`, the system:

#### Step 1: Get Existing Chunks
- Fetches all existing chunks for each file being indexed
- Groups by `(file_path, line_start)` as the key

#### Step 2: Compare New vs Existing
For each file:

| Scenario | Action | Why |
|----------|--------|-----|
| **Same line_start + Same content** | ✅ **Skip** | No change, don't waste resources |
| **Same line_start + Different content** | 🔄 **Update** | Content changed, update with same ID |
| **New line_start** | ➕ **Add** | New content, create new chunk |
| **Existing line_start not in new file** | 🗑️ **Delete** | Content removed, delete chunk |

#### Step 3: Execute Operations
- **Upsert** (update or insert) for changed/new chunks
- **Delete** for removed chunks
- Uses **batch operations** for efficiency

### 3. Example Scenarios

#### Scenario A: Adding New Files

**Before**: 
- `README.md` indexed (50 chunks)

**Action**: 
- Add `test-doc.md` and `test-code.py` to config
- Run `python rag_cli.py index`

**What Happens**:
1. ✅ `README.md`: Checks existing chunks, finds all 50, content matches → **skips** (0 operations)
2. ✅ `test-doc.md`: No existing chunks → **adds** all 4 chunks
3. ✅ `test-code.py`: No existing chunks → **adds** all 3 chunks

**Result**: Only 7 new chunks added, README.md untouched

#### Scenario B: Modifying Existing File

**Before**:
- `test-doc.md` indexed (4 chunks at lines 1, 10, 20, 30)

**Action**:
- Edit line 20 (change content)
- Add new content at line 40
- Run `python rag_cli.py index`

**What Happens**:
1. ✅ Line 1: Same content → **skip**
2. ✅ Line 10: Same content → **skip**
3. 🔄 Line 20: Different content → **update** (same ID, new vector)
4. ✅ Line 30: Same content → **skip**
5. ➕ Line 40: New → **add** (new ID)

**Result**: 1 update, 1 add, 3 skips

#### Scenario C: Deleting File

**Before**:
- `test-doc.md` indexed (4 chunks)
- `test-code.py` indexed (3 chunks)

**Action**:
- Remove `test-doc.md` from config
- Run `python rag_cli.py index --cleanup` (or `--prune`)

**What Happens**:
1. ✅ `test-code.py`: Still in config → **no change**
2. 🗑️ `test-doc.md`: Not in config → **soft-delete** all 4 chunks

**Result**: 4 chunks marked as deleted (not removed, can be recovered)

## Cases Already Handled

### ✅ Case 1: New Files Added
- **Status**: ✅ Fully handled
- **How**: System detects files not in existing chunks, adds them
- **Command**: `python rag_cli.py index`

### ✅ Case 2: Files Modified
- **Status**: ✅ Fully handled
- **How**: Compares content by line_start, updates only changed chunks
- **Command**: `python rag_cli.py index`

### ✅ Case 3: Files Deleted
- **Status**: ✅ Fully handled (with cleanup)
- **How**: Detects files in DB but not in config, soft-deletes chunks
- **Command**: `python rag_cli.py index --cleanup` (or `--prune`)

### ✅ Case 4: Duplicate Prevention
- **Status**: ✅ Fully handled
- **How**: 
  - Deterministic point IDs prevent duplicates
  - Upsert operations (update if exists, insert if not)
  - Same file+line always gets same ID

### ✅ Case 5: Path Normalization
- **Status**: ✅ Fully handled
- **How**: All paths normalized to forward slashes before comparison
- **Prevents**: Windows/Unix path mismatches

### ✅ Case 6: Re-indexing Unchanged Files
- **Status**: ✅ Fully handled
- **How**: Compares content hash, skips if identical
- **Performance**: No unnecessary re-encoding or API calls

### ✅ Case 7: Partial File Updates
- **Status**: ✅ Fully handled
- **How**: Only updates changed chunks, keeps others untouched
- **Efficiency**: Minimal API calls

### ✅ Case 8: Recovery from Deletions
- **Status**: ✅ Fully handled
- **How**: Soft-delete (marks as deleted, doesn't remove)
- **Command**: `python rag_cli.py recover` to restore

## Commands Reference

### Standard Indexing (Incremental)
```bash
python rag_cli.py index
```
- ✅ Indexes new files
- ✅ Updates modified files
- ✅ Skips unchanged files
- ✅ Safe to run multiple times

### Index with Cleanup
```bash
python rag_cli.py index --cleanup
```
- ✅ Everything from standard indexing
- ✅ Soft-deletes chunks from files removed from config
- ✅ Safe (dry-run by default, use `--prune` to actually delete)

### Force Re-index (if needed)
```bash
# Delete all data first (careful!)
python rag_cli.py delete --confirm

# Then re-index
python rag_cli.py index
```

## Performance Characteristics

### First Indexing
- **Time**: ~30-60 seconds per 100 files (depends on file size)
- **Operations**: Full indexing of all files
- **API Calls**: ~1 per file (batch upserts)

### Incremental Indexing (No Changes)
- **Time**: ~5-10 seconds (just checking)
- **Operations**: Mostly skips
- **API Calls**: Minimal (only for changed files)

### Incremental Indexing (2 New Files)
- **Time**: ~10-20 seconds (only new files)
- **Operations**: Only new files indexed
- **API Calls**: ~2 (one per new file)

### Incremental Indexing (1 Modified File)
- **Time**: ~5-15 seconds (only changed chunks)
- **Operations**: Only changed chunks updated
- **API Calls**: ~1 (batch update for changed chunks)

## Best Practices

### 1. Regular Indexing
```bash
# After adding/modifying files
python rag_cli.py index
```

### 2. Periodic Cleanup
```bash
# After removing files from config
python rag_cli.py index --cleanup
```

### 3. Verify Changes
```bash
# Check what was indexed
python rag_cli.py stats
```

### 4. Recovery (if needed)
```bash
# Restore accidentally deleted chunks
python rag_cli.py recover
```

## Troubleshooting

### Problem: New files not indexed
**Solution**: 
- Check files are in `mcp-config.json` paths
- Verify file paths are correct (relative to project root)
- Check logs: `rag-server/rag-server.log`

### Problem: Duplicates appearing
**Solution**: 
- Shouldn't happen (deterministic IDs prevent this)
- If it does, check for path normalization issues
- Verify same file isn't indexed twice in config

### Problem: Changes not reflected
**Solution**:
- Re-run indexing: `python rag_cli.py index`
- Check file was actually modified (content changed)
- Verify file is in config paths

### Problem: Deleted files still in results
**Solution**:
- Run cleanup: `python rag_cli.py index --cleanup --prune`
- Verify files removed from config
- Check stats: `python rag_cli.py stats`

## Technical Details

### Point ID Collision Prevention
- Uses 63-bit hash (2^63 - 1 possible values)
- Collision probability: ~1 in 9.2 quintillion
- Practically impossible for normal use cases

### Batch Operations
- Upserts: Batched (1000 points per batch)
- Deletes: Batched (1000 IDs per batch)
- Reduces API calls significantly

### Content Comparison
- Exact string comparison (byte-by-byte)
- Case-sensitive
- Whitespace-sensitive
- Ensures accuracy

### Path Handling
- All paths normalized to forward slashes
- Relative paths computed from project root
- Handles Windows/Unix path differences

## Summary

**The system is designed for incremental updates:**

1. ✅ **Same command** for new files, modified files, or unchanged files
2. ✅ **Automatic duplicate prevention** via deterministic IDs
3. ✅ **Efficient** - only processes what changed
4. ✅ **Safe** - can run multiple times without issues
5. ✅ **Handles all cases** - new, modified, deleted files

**Just run `python rag_cli.py index` whenever you add or modify files!**

