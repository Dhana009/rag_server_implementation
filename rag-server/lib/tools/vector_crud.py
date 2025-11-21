"""
QUADRANTDB Tools: Minimal, clean, efficient vector database operations.

Six core tools:
1. add_vector - Store new data (text/code/log) with embeddings + metadata
2. get_vector - Retrieve a stored vector item by ID
3. update_vector - Update text/metadata for an existing vector entry
4. delete_vector - Delete a stored vector entry
5. search_similar - Semantic similarity search using embeddings
6. search_by_metadata - Retrieve items by tags/category/file/error-type, etc.
"""

import json
import logging
import time
from typing import List, Dict, Optional, Any
from mcp.types import Tool

logger = logging.getLogger(__name__)

try:
    from ..core.vector_store import (
        HybridVectorStore,
        VectorStoreError,
        ValidationError,
        PointNotFoundError,
        DimensionMismatchError,
        BatchLimitExceededError
    )
    from ..config import load_config
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.core.vector_store import (
        HybridVectorStore,
        VectorStoreError,
        ValidationError,
        PointNotFoundError,
        DimensionMismatchError,
        BatchLimitExceededError
    )
    from config import load_config
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue


# Error suggestion mapping
ERROR_SUGGESTIONS = {
    "VALIDATION_ERROR": [
        "Check that all required fields are provided",
        "Verify field types match expected format",
        "Review input schema documentation"
    ],
    "DIMENSION_MISMATCH": [
        "Ensure vector has correct dimension (384 for default embedder)",
        "Check embedding model configuration",
        "Verify vector format is correct"
    ],
    "POINT_NOT_FOUND": [
        "Verify vector ID exists in collection",
        "Check if vector was deleted",
        "Use search_similar or search_by_metadata to find vector IDs"
    ],
    "COLLECTION_ERROR": [
        "Verify collection exists",
        "Check cloud Qdrant connection",
        "Review collection configuration"
    ]
}


def _create_response(success: bool, data: Any = None, metadata: Dict = None, 
                     errors: List = None, version: str = None) -> str:
    """Create consistent JSON response structure."""
    response = {
        "success": success,
        "data": data,
        "metadata": metadata or {},
        "errors": errors or []
    }
    if version:
        response["version"] = version
    return json.dumps(response, indent=2)


def _format_error(error: Exception) -> Dict:
    """Format exception as structured error."""
    if isinstance(error, VectorStoreError):
        return {
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "suggestions": error.suggestions or ERROR_SUGGESTIONS.get(error.code, [])
        }
    else:
        return {
            "code": "UNKNOWN_ERROR",
            "message": str(error),
            "details": {},
            "suggestions": ["Check logs for more details", "Verify input parameters"]
        }


# QUADRANTDB Tools - Six Core Operations

def add_vector(content: str = "", metadata: Dict = None, vector: Optional[List[float]] = None) -> str:
    """
    Store new data (text/code/log) with embeddings + metadata.
    
    Args:
        content: Text/code/log content to store (auto-embedded if vector not provided)
        metadata: Optional metadata dict (tags, category, file_path, error_type, etc.)
        vector: Optional pre-computed vector (384 dimensions). If provided, content is ignored for embedding.
    
    Returns:
        JSON response with vector ID and success status
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Validate input
        if not content and not vector:
            raise ValidationError(
                code="VALIDATION_ERROR",
                message="Either 'content' or 'vector' must be provided",
                details={},
                suggestions=ERROR_SUGGESTIONS["VALIDATION_ERROR"]
            )
        
        # Get or generate vector
        if vector:
            store.validate_vector(vector)
            # Use content for ID generation if available, otherwise use vector hash
            content_for_id = content if content else str(hash(tuple(vector)))
        else:
            if not content.strip():
                raise ValidationError(
                    code="VALIDATION_ERROR",
                    message="Content cannot be empty",
                    details={},
                    suggestions=ERROR_SUGGESTIONS["VALIDATION_ERROR"]
                )
            vector = store.encode_content(content)
            content_for_id = content
        
        # Prepare metadata
        metadata = metadata or {}
        metadata.setdefault("is_deleted", False)
        if content and "content" not in metadata:
            metadata["content"] = content
        
        # Generate ID
        file_path = metadata.get("file_path", "")
        line_start = metadata.get("line_start", 0)
        vector_id = store.generate_point_id(content_for_id, file_path, line_start)
        
        # Create point
        point_struct = store.create_point_struct(vector_id, vector, metadata)
        
        # Upsert to cloud collection
        store.cloud_client.upsert(
            collection_name=store.cloud_collection,
            points=[point_struct]
        )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ add_vector completed in {elapsed:.2f}s: vector_id={vector_id}")
        
        return _create_response(
            success=True,
            data={
                "vector_id": vector_id,
                "metadata": metadata
            },
            metadata={
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "add_vector"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ add_vector failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "add_vector"},
            errors=[_format_error(e)]
        )


def get_vector(vector_id: int, include_vector: bool = False) -> str:
    """
    Retrieve a stored vector item by ID.
    
    Args:
        vector_id: Vector ID to retrieve
        include_vector: Whether to include the vector in response (default: False)
    
    Returns:
        JSON response with vector data and metadata
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Retrieve point
        points = store.cloud_client.retrieve(
            collection_name=store.cloud_collection,
            ids=[vector_id],
            with_vectors=include_vector
        )
        
        if not points:
            raise PointNotFoundError(
                code="POINT_NOT_FOUND",
                message=f"Vector with ID {vector_id} not found",
                details={"vector_id": vector_id},
                suggestions=ERROR_SUGGESTIONS["POINT_NOT_FOUND"]
            )
        
        point = points[0]
        result = {
            "vector_id": point.id,
            "metadata": point.payload
        }
        
        if include_vector and point.vector:
            result["vector"] = list(point.vector)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ get_vector completed in {elapsed:.2f}s: vector_id={vector_id}")
        
        return _create_response(
            success=True,
            data=result,
            metadata={
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "get_vector"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ get_vector failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "get_vector"},
            errors=[_format_error(e)]
        )


def update_vector(vector_id: int, content: Optional[str] = None, 
                 metadata: Optional[Dict] = None, vector: Optional[List[float]] = None) -> str:
    """
    Update text/metadata for an existing vector entry.
    
    Args:
        vector_id: Vector ID to update
        content: Optional new content (re-embeds if provided)
        metadata: Optional updated metadata (merged with existing)
        vector: Optional new vector (384 dimensions)
    
    Returns:
        JSON response with success status
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Check if point exists
        existing = store.cloud_client.retrieve(
            collection_name=store.cloud_collection,
            ids=[vector_id]
        )
        
        if not existing:
            raise PointNotFoundError(
                code="POINT_NOT_FOUND",
                message=f"Vector with ID {vector_id} not found",
                details={"vector_id": vector_id},
                suggestions=ERROR_SUGGESTIONS["POINT_NOT_FOUND"]
            )
        
        existing_point = existing[0]
        existing_payload = existing_point.payload or {}
        
        # Determine new vector
        if vector:
            store.validate_vector(vector)
            new_vector = vector
        elif content:
            new_vector = store.encode_content(content)
        else:
            # Keep existing vector
            if existing_point.vector:
                new_vector = list(existing_point.vector)
            else:
                raise ValidationError(
                    code="VALIDATION_ERROR",
                    message="Must provide either 'content' or 'vector' for update",
                    details={},
                    suggestions=ERROR_SUGGESTIONS["VALIDATION_ERROR"]
                )
        
        # Merge metadata
        updated_payload = existing_payload.copy()
        if metadata:
            updated_payload.update(metadata)
        if content:
            updated_payload["content"] = content
        updated_payload.setdefault("is_deleted", False)
        
        # Create updated point
        point_struct = store.create_point_struct(vector_id, new_vector, updated_payload)
        
        # Upsert
        store.cloud_client.upsert(
            collection_name=store.cloud_collection,
            points=[point_struct]
        )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ update_vector completed in {elapsed:.2f}s: vector_id={vector_id}")
        
        return _create_response(
            success=True,
            data={
                "vector_id": vector_id,
                "metadata": updated_payload
            },
            metadata={
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "update_vector"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ update_vector failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "update_vector"},
            errors=[_format_error(e)]
        )


def delete_vector(vector_id: int, soft_delete: bool = False) -> str:
    """
    Delete a stored vector entry.
    
    Args:
        vector_id: Vector ID to delete
        soft_delete: If True, mark as deleted (is_deleted=True). If False, hard delete (permanent removal).
    
    Returns:
        JSON response with success status
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Check if point exists
        existing = store.cloud_client.retrieve(
            collection_name=store.cloud_collection,
            ids=[vector_id]
        )
        
        if not existing:
            raise PointNotFoundError(
                code="POINT_NOT_FOUND",
                message=f"Vector with ID {vector_id} not found",
                details={"vector_id": vector_id},
                suggestions=ERROR_SUGGESTIONS["POINT_NOT_FOUND"]
            )
        
        # Execute deletion
        if soft_delete:
            # Soft delete: mark as deleted
            store.cloud_client.set_payload(
                collection_name=store.cloud_collection,
                payload={"is_deleted": True},
                points=[vector_id]
            )
        else:
            # Hard delete: remove from collection
            store.cloud_client.delete(
                collection_name=store.cloud_collection,
                points_selector=[vector_id]
            )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ delete_vector completed in {elapsed:.2f}s: vector_id={vector_id}, soft={soft_delete}")
        
        return _create_response(
            success=True,
            data={
                "vector_id": vector_id,
                "soft_delete": soft_delete
            },
            metadata={
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "delete_vector"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ delete_vector failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "delete_vector"},
            errors=[_format_error(e)]
        )


def search_similar(query: str, top_k: int = 10, vector: Optional[List[float]] = None,
                  filter: Optional[Dict] = None) -> str:
    """
    Semantic similarity search using embeddings.
    
    Args:
        query: Search query text (auto-embedded if vector not provided)
        top_k: Number of results to return (default: 10, max: 100)
        vector: Optional pre-computed query vector (384 dimensions)
        filter: Optional metadata filter dict (e.g., {"must": [{"key": "category", "match": "error"}]})
    
    Returns:
        JSON response with similar vectors and scores
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Validate top_k
        if top_k > 100:
            top_k = 100
            logger.warning(f"top_k exceeds maximum, using 100")
        
        # Get query vector
        if vector:
            store.validate_vector(vector)
            query_vector = vector
        else:
            if not query.strip():
                raise ValidationError(
                    code="VALIDATION_ERROR",
                    message="Query cannot be empty",
                    details={},
                    suggestions=ERROR_SUGGESTIONS["VALIDATION_ERROR"]
                )
            query_vector = store.encode_content(query)
        
        # Build filter if provided
        qdrant_filter = None
        if filter:
            qdrant_filter = store.parse_filter(filter)
        
        # Search
        from qdrant_client.models import NearestQuery
        search_results = store.cloud_client.query_points(
            collection_name=store.cloud_collection,
            query=NearestQuery(nearest=query_vector),
            limit=top_k,
            query_filter=qdrant_filter
        )
        
        # Format results
        results = []
        for point in search_results.points:
            # Skip soft-deleted
            if point.payload.get('is_deleted', False):
                continue
            
            result = {
                "vector_id": point.id,
                "score": getattr(point, 'score', 0.0),
                "metadata": point.payload
            }
            results.append(result)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ search_similar completed in {elapsed:.2f}s: {len(results)} results")
        
        return _create_response(
            success=True,
            data={
                "results": results,
                "count": len(results),
                "query": query
            },
            metadata={
                "count": len(results),
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "search_similar"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ search_similar failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "search_similar"},
            errors=[_format_error(e)]
        )


def search_by_metadata(filter: Dict, limit: int = 10, offset: int = 0) -> str:
    """
    Retrieve items by tags/category/file/error-type, etc.
    
    Args:
        filter: Metadata filter dict with must/should/must_not conditions
                Example: {"must": [{"key": "category", "match": "error"}, {"key": "file_path", "match": "test.py"}]}
        limit: Number of results (default: 10, max: 1000)
        offset: Pagination offset (default: 0)
    
    Returns:
        JSON response with matching vectors
    """
    start_time = time.time()
    try:
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Validate limit
        if limit > 1000:
            limit = 1000
            logger.warning(f"Limit exceeds maximum, using 1000")
        
        # Parse filter
        qdrant_filter = store.parse_filter(filter)
        
        # Scroll with filter
        points, _ = store.cloud_client.scroll(
            collection_name=store.cloud_collection,
            scroll_filter=qdrant_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results (filter out soft-deleted)
        results = []
        for point in points:
            if not point.payload.get('is_deleted', False):
                results.append({
                    "vector_id": point.id,
                    "metadata": point.payload
                })
        
        elapsed = time.time() - start_time
        logger.info(f"✅ search_by_metadata completed in {elapsed:.2f}s: {len(results)} results")
        
        return _create_response(
            success=True,
            data={
                "results": results,
                "count": len(results),
                "limit": limit,
                "offset": offset
            },
            metadata={
                "count": len(results),
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "search_by_metadata"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ search_by_metadata failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "search_by_metadata"},
            errors=[_format_error(e)]
        )


# MCP Tool Definitions

add_vector_tool_mcp = Tool(
    name="add_vector",
    description="Store new data (text/code/log) with embeddings + metadata. Auto-embeds content if vector not provided. Returns generated vector ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Text/code/log content to store (auto-embedded if vector not provided). Optional if vector is provided.",
                "default": ""
            },
            "metadata": {
                "type": "object",
                "description": "Optional metadata dict (tags, category, file_path, error_type, etc.)",
                "default": {}
            },
            "vector": {
                "type": "array",
                "description": "Optional pre-computed vector (384 dimensions). If provided, content is ignored for embedding.",
                "items": {"type": "number"}
            }
        },
        "required": []
    }
)

get_vector_tool_mcp = Tool(
    name="get_vector",
    description="Retrieve a stored vector item by ID. Returns vector data with metadata.",
    inputSchema={
        "type": "object",
        "properties": {
            "vector_id": {
                "type": "integer",
                "description": "Vector ID to retrieve"
            },
            "include_vector": {
                "type": "boolean",
                "description": "Whether to include the vector in response",
                "default": False
            }
        },
        "required": ["vector_id"]
    }
)

update_vector_tool_mcp = Tool(
    name="update_vector",
    description="Update text/metadata for an existing vector entry. Merges metadata with existing. Re-embeds if content changes.",
    inputSchema={
        "type": "object",
        "properties": {
            "vector_id": {
                "type": "integer",
                "description": "Vector ID to update"
            },
            "content": {
                "type": "string",
                "description": "Optional new content (re-embeds if provided)"
            },
            "metadata": {
                "type": "object",
                "description": "Optional updated metadata (merged with existing)"
            },
            "vector": {
                "type": "array",
                "description": "Optional new vector (384 dimensions)",
                "items": {"type": "number"}
            }
        },
        "required": ["vector_id"]
    }
)

delete_vector_tool_mcp = Tool(
    name="delete_vector",
    description="Delete a stored vector entry. Supports soft-delete (mark as deleted) and hard-delete (permanent removal).",
    inputSchema={
        "type": "object",
        "properties": {
            "vector_id": {
                "type": "integer",
                "description": "Vector ID to delete"
            },
            "soft_delete": {
                "type": "boolean",
                "description": "If True, mark as deleted. If False, hard delete (permanent removal).",
                "default": False
            }
        },
        "required": ["vector_id"]
    }
)

search_similar_tool_mcp = Tool(
    name="search_similar",
    description="Semantic similarity search using embeddings. Returns similar vectors with similarity scores.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query text (auto-embedded if vector not provided)"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            },
            "vector": {
                "type": "array",
                "description": "Optional pre-computed query vector (384 dimensions)",
                "items": {"type": "number"}
            },
            "filter": {
                "type": "object",
                "description": "Optional metadata filter dict (e.g., {\"must\": [{\"key\": \"category\", \"match\": \"error\"}]})"
            }
        },
        "required": []
    }
)

search_by_metadata_tool_mcp = Tool(
    name="search_by_metadata",
    description="Retrieve items by tags/category/file/error-type, etc. Supports pagination.",
    inputSchema={
        "type": "object",
        "properties": {
            "filter": {
                "type": "object",
                "description": "Metadata filter dict with must/should/must_not conditions. Example: {\"must\": [{\"key\": \"category\", \"match\": \"error\"}]}",
                "properties": {
                    "must": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "match": {"description": "Value to match"}
                            }
                        }
                    }
                }
            },
            "limit": {
                "type": "integer",
                "description": "Number of results",
                "default": 10,
                "minimum": 1,
                "maximum": 1000
            },
            "offset": {
                "type": "integer",
                "description": "Pagination offset",
                "default": 0,
                "minimum": 0
            }
        },
        "required": ["filter"]
    }
)
