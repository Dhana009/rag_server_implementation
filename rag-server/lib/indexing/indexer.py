from pathlib import Path
from typing import List, Dict
import logging
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from lib.core.vector_store import HybridVectorStore
    from config import Config
except ImportError:
    from lib.core.vector_store import HybridVectorStore
    from config import Config

logger = logging.getLogger(__name__)

def _detect_doc_type(file_path: str) -> str:
    """Detect doc type from path"""
    if 'proposal-plan/development' in file_path or 'proposal-plan/testing' in file_path:
        return 'policy'
    elif 'software-development-life-cycle' in file_path:
        return 'sdlc'
    elif 'complete-flows' in file_path:
        return 'flow'
    elif 'infrastructure' in file_path:
        return 'infrastructure'
    elif 'Discussion' in file_path:
        return 'decision'
    return 'other'

def _is_numbered_list(lines: List[str], start_idx: int) -> bool:
    """Detect if lines starting at start_idx form a numbered list."""
    if start_idx >= len(lines):
        return False
    line = lines[start_idx].strip()
    # Check for pattern like "1. ", "2. ", etc.
    return len(line) > 2 and line[0].isdigit() and line[1] == '.'

def _is_table_line(line: str) -> bool:
    """Detect if line is part of a markdown table."""
    return '|' in line

def _get_list_length(lines: List[str], start_idx: int) -> int:
    """Get number of items in a numbered list starting at start_idx."""
    count = 0
    i = start_idx
    while i < len(lines):
        line = lines[i].strip()
        if not line or not (line[0].isdigit() and len(line) > 2 and line[1] == '.'):
            break
        count += 1
        i += 1
    return count

def chunk_markdown(content: str, file_path: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
    """
    Enhanced chunking: preserve structure (lists, tables), chunk by sections.
    
    Strategy:
    - Chunk by ## headers (primary)
    - Preserve numbered lists (keep together)
    - Preserve markdown tables (keep together)
    - Only split if content > chunk_size
    
    Returns: List of {
        "content": str,
        "line_start": int,
        "line_end": int,
        "metadata": {
            "section": str,
            "doc_type": str,
            "content_type": str,  # "list", "table", "text", "code"
            "list_length": int | None,
            "is_complete": bool
        }
    }
    """
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_section = "Introduction"
    line_start = 1
    
    for i, line in enumerate(lines, 1):
        # Detect section headers
        if line.startswith('## '):
            # Save current chunk if exists
            if current_chunk:
                chunks.append(_create_chunk(current_chunk, line_start, i - 1, current_section, file_path))
            # Start new chunk
            current_chunk = [line]
            current_section = line[3:].strip()
            line_start = i
        else:
            current_chunk.append(line)
            chunk_text = '\n'.join(current_chunk)
            
            # Check if this is a numbered list or table - keep it together
            if _is_numbered_list(current_chunk, 0) or _is_table_line('\n'.join(current_chunk)):
                # For lists/tables, only split if MUCH larger than chunk_size
                if len(chunk_text) > chunk_size * 2:
                    chunks.append(_create_chunk(current_chunk[:-overlap], line_start, i, current_section, file_path))
                    current_chunk = current_chunk[-overlap:]
                    line_start = i - overlap
            else:
                # For regular text, normal splitting
                if len(chunk_text) > chunk_size:
                    chunks.append(_create_chunk(current_chunk[:-overlap], line_start, i, current_section, file_path))
                    current_chunk = current_chunk[-overlap:]
                    line_start = i - overlap
    
    # Add final chunk
    if current_chunk:
        chunks.append(_create_chunk(current_chunk, line_start, len(lines), current_section, file_path))
    
    return chunks

def _create_chunk(lines: List[str], line_start: int, line_end: int, section: str, file_path: str) -> Dict:
    """Create a chunk with enhanced metadata."""
    content = '\n'.join(lines)
    
    # Detect content type
    if lines and _is_numbered_list(lines, 0):
        content_type = "list"
        list_length = _get_list_length(lines, 0)
        is_complete = True
    elif any(_is_table_line(line) for line in lines):
        content_type = "table"
        list_length = None
        is_complete = True
    elif any(line.strip().startswith('```') for line in lines):
        content_type = "code"
        list_length = None
        is_complete = True
    else:
        content_type = "text"
        list_length = None
        is_complete = False
    
    return {
        "content": content,
        "line_start": line_start,
        "line_end": line_end,
        "metadata": {
            "section": section,
            "doc_type": _detect_doc_type(file_path),
            "content_type": content_type,
            "list_length": list_length,
            "is_complete": is_complete
        }
    }

def index_all_documents(vector_store: HybridVectorStore, config: Config) -> Dict[str, int]:
    """
    Index all documents from config.cloud_docs and config.local_docs
    
    Returns: {"cloud": count, "local": count, "errors": count}
    """
    base_path = config.project_root
    stats = {"cloud": 0, "local": 0, "errors": 0}
    
    # Index cloud docs
    for pattern in config.cloud_docs:
        for file_path in base_path.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.md':
                try:
                    rel_path = str(file_path.relative_to(base_path))
                    logger.info(f"\n{'='*70}")
                    logger.info(f"📝 Indexing: {rel_path}")
                    logger.info(f"{'='*70}")
                    
                    content = file_path.read_text(encoding='utf-8')
                    chunks = chunk_markdown(content, rel_path, 
                                           chunk_size=config.chunk_size, 
                                           overlap=config.chunk_overlap)
                    logger.info(f"   Generated {len(chunks)} chunks from file")
                    
                    if vector_store.index_doc(rel_path, "cloud", chunks):
                        stats["cloud"] += len(chunks)
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Failed to index {file_path}: {e}")
                    stats["errors"] += 1
    
    # Index local docs (mirror cloud + local-only)
    # First mirror all cloud docs to local
    for pattern in config.cloud_docs:
        for file_path in base_path.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.md':
                try:
                    rel_path = str(file_path.relative_to(base_path))
                    logger.info(f"\n{'='*70}")
                    logger.info(f"📝 Indexing: {rel_path} (local)")
                    logger.info(f"{'='*70}")
                    
                    content = file_path.read_text(encoding='utf-8')
                    chunks = chunk_markdown(content, rel_path,
                                           chunk_size=config.chunk_size,
                                           overlap=config.chunk_overlap)
                    logger.info(f"   Generated {len(chunks)} chunks from file")
                    
                    if vector_store.index_doc(rel_path, "local", chunks):
                        stats["local"] += len(chunks)
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Failed to mirror {file_path} to local: {e}")
                    stats["errors"] += 1
    
    # Index local-only docs
    for pattern in config.local_docs:
        for file_path in base_path.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.md':
                try:
                    content = file_path.read_text(encoding='utf-8')
                    chunks = chunk_markdown(content, str(file_path.relative_to(base_path)),
                                           chunk_size=config.chunk_size,
                                           overlap=config.chunk_overlap)
                    rel_path = str(file_path.relative_to(base_path))
                    if vector_store.index_doc(rel_path, "local", chunks):
                        stats["local"] += len(chunks)
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Failed to index local doc {file_path}: {e}")
                    stats["errors"] += 1
    
    return stats

