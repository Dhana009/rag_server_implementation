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
import sys
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
    from qdrant_client.http.exceptions import UnexpectedResponse
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
    from qdrant_client.http.exceptions import UnexpectedResponse


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


def _convert_vector_ids_to_strings(obj: Any) -> Any:
    """
    Recursively convert all vector_id fields from int to string.
    This prevents JavaScript number precision loss for large integers (19+ digits).
    JavaScript MAX_SAFE_INTEGER is 2^53-1 (16 digits), but our IDs are 19 digits.
    """
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key == "vector_id" and isinstance(value, int):
                # Convert vector_id to string to avoid JS precision loss
                result[key] = str(value)
            elif key == "vector_id" and isinstance(value, (list, tuple)):
                # Handle list of vector_ids
                result[key] = [str(v) if isinstance(v, int) else v for v in value]
            else:
                result[key] = _convert_vector_ids_to_strings(value)
        return result
    elif isinstance(obj, list):
        return [_convert_vector_ids_to_strings(item) for item in obj]
    else:
        return obj


def _create_response(success: bool, data: Any = None, metadata: Dict = None, 
                     errors: List = None, version: str = None) -> str:
    """Create consistent JSON response structure."""
    # Convert vector_id fields to strings to prevent JavaScript precision loss
    if data is not None:
        data = _convert_vector_ids_to_strings(data)
    
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


def get_vector(vector_id, include_vector: bool = False) -> str:
    """
    Retrieve a stored vector item by ID.
    
    Args:
        vector_id: Vector ID to retrieve (int or string - accepts string to handle JS precision issues)
        include_vector: Whether to include the vector in response (default: False)
    
    Returns:
        JSON response with vector data and metadata
    """
    start_time = time.time()
    try:
        # Log received vector_id for debugging
        original_vector_id = vector_id
        original_type = type(vector_id).__name__
        logger.debug(f"get_vector received: vector_id={vector_id}, type={original_type}")
        
        # Convert string to int if needed (handles JS precision loss workaround)
        if isinstance(vector_id, str):
            try:
                vector_id = int(vector_id)
                logger.debug(f"Converted string to int: {vector_id}")
            except (ValueError, TypeError):
                raise ValidationError(
                    code="VALIDATION_ERROR",
                    message=f"Invalid vector_id format: {vector_id}. Must be an integer or numeric string.",
                    details={"vector_id": vector_id},
                    suggestions=["Provide a valid integer vector_id", "Use search_similar to find vector IDs"]
                )
        elif not isinstance(vector_id, int):
            raise ValidationError(
                code="VALIDATION_ERROR",
                message=f"Invalid vector_id type: {type(vector_id).__name__}. Must be int or str.",
                details={"vector_id": vector_id, "type": type(vector_id).__name__},
                suggestions=["Provide vector_id as integer or string"]
            )
        
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
            # Check if this might be a precision-corrupted ID (ends in 000)
            error_msg = f"Vector with ID {vector_id} not found"
            suggestions = list(ERROR_SUGGESTIONS["POINT_NOT_FOUND"])
            
            # If ID ends in 000 and is 19 digits, it might be precision-corrupted
            if isinstance(vector_id, int) and len(str(vector_id)) >= 15 and str(vector_id).endswith("000"):
                error_msg += f" (Possible JavaScript precision loss - received {original_type} with value {original_vector_id})"
                suggestions.insert(0, "This ID may have lost precision due to JavaScript number conversion. Use search_similar to find the correct vector ID.")
                suggestions.insert(1, "Vector IDs are returned as strings to prevent precision loss - preserve the string format when using the ID.")
            
            raise PointNotFoundError(
                code="POINT_NOT_FOUND",
                message=error_msg,
                details={
                    "vector_id": vector_id,
                    "original_vector_id": str(original_vector_id),
                    "original_type": original_type,
                    "received_type": type(vector_id).__name__
                },
                suggestions=suggestions
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


def update_vector(vector_id, content: Optional[str] = None, 
                 metadata: Optional[Dict] = None, vector: Optional[List[float]] = None) -> str:
    """
    Update text/metadata for an existing vector entry.
    
    Args:
        vector_id: Vector ID to update (int or string - accepts string to handle JS precision issues)
        content: Optional new content (re-embeds if provided)
        metadata: Optional updated metadata (merged with existing)
        vector: Optional new vector (384 dimensions)
    
    Returns:
        JSON response with success status
    """
    start_time = time.time()
    try:
        # Convert string to int if needed (handles JS precision loss workaround)
        if isinstance(vector_id, str):
            try:
                vector_id = int(vector_id)
            except (ValueError, TypeError):
                raise ValidationError(
                    code="VALIDATION_ERROR",
                    message=f"Invalid vector_id format: {vector_id}. Must be an integer or numeric string.",
                    details={"vector_id": vector_id},
                    suggestions=["Provide a valid integer vector_id", "Use search_similar to find vector IDs"]
                )
        elif not isinstance(vector_id, int):
            raise ValidationError(
                code="VALIDATION_ERROR",
                message=f"Invalid vector_id type: {type(vector_id).__name__}. Must be int or str.",
                details={"vector_id": vector_id, "type": type(vector_id).__name__},
                suggestions=["Provide vector_id as integer or string"]
            )
        
        config = load_config()
        store = HybridVectorStore(config)
        store.ensure_collection_exists("cloud")
        
        # Check if point exists (retrieve with vector to allow metadata-only updates)
        existing = store.cloud_client.retrieve(
            collection_name=store.cloud_collection,
            ids=[vector_id],
            with_vectors=True  # Need vector for metadata-only updates
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
            # Metadata-only update: keep existing vector
            if existing_point.vector:
                new_vector = list(existing_point.vector)
            else:
                # This shouldn't happen, but handle gracefully
                # Try to get vector from existing content if available
                existing_content = existing_payload.get("content", "")
                if existing_content:
                    new_vector = store.encode_content(existing_content)
                else:
                    raise ValidationError(
                        code="VALIDATION_ERROR",
                        message="Cannot update: no existing vector found and no content/vector provided. Provide either 'content' or 'vector' for update.",
                        details={"vector_id": vector_id},
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


def delete_vector(vector_id, soft_delete: bool = False) -> str:
    """
    Delete a stored vector entry.
    
    Args:
        vector_id: Vector ID to delete (int or string - accepts string to handle JS precision issues)
        soft_delete: If True, mark as deleted (is_deleted=True). If False, hard delete (permanent removal).
    
    Returns:
        JSON response with success status
    """
    start_time = time.time()
    try:
        # Convert string to int if needed (handles JS precision loss workaround)
        if isinstance(vector_id, str):
            try:
                vector_id = int(vector_id)
            except (ValueError, TypeError):
                raise ValidationError(
                    code="VALIDATION_ERROR",
                    message=f"Invalid vector_id format: {vector_id}. Must be an integer or numeric string.",
                    details={"vector_id": vector_id},
                    suggestions=["Provide a valid integer vector_id", "Use search_similar to find vector IDs"]
                )
        elif not isinstance(vector_id, int):
            raise ValidationError(
                code="VALIDATION_ERROR",
                message=f"Invalid vector_id type: {type(vector_id).__name__}. Must be int or str.",
                details={"vector_id": vector_id, "type": type(vector_id).__name__},
                suggestions=["Provide vector_id as integer or string"]
            )
        
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


def delete_all(collection: str = "cloud", confirm: bool = False) -> str:
    """
    Delete all vectors from a collection.
    
    ⚠️  WARNING: This permanently deletes ALL indexed data!
    
    Args:
        collection: Target collection ("cloud" or "local")
        confirm: Must be True to actually delete (safety check)
    
    Returns:
        JSON response with success status and deletion count
    """
    start_time = time.time()
    try:
        if not confirm:
            raise ValidationError(
                code="VALIDATION_ERROR",
                message="delete_all requires confirm=True for safety. This operation permanently deletes ALL data!",
                details={"collection": collection, "confirm": confirm},
                suggestions=["Set confirm=True if you really want to delete all data", "This operation cannot be undone"]
            )
        
        config = load_config()
        store = HybridVectorStore(config)
        
        # Validate collection
        if collection not in ["cloud", "local"]:
            raise ValidationError(
                code="VALIDATION_ERROR",
                message=f"Invalid collection: {collection}. Must be 'cloud' or 'local'",
                details={"collection": collection},
                suggestions=["Use 'cloud' or 'local' as collection name"]
            )
        
        # Check if local is enabled when trying to use it
        if collection == "local" and not store.local_enabled:
            raise ValidationError(
                code="VALIDATION_ERROR",
                message="Local storage is disabled. Cannot delete from local collection.",
                details={"collection": collection, "local_enabled": store.local_enabled},
                suggestions=["Use 'cloud' collection instead", "Enable local storage in config"]
            )
        
        # Get client and collection name
        client = store.cloud_client if collection == "cloud" else store.local_client
        coll_name = store.cloud_collection if collection == "cloud" else store.local_collection
        
        # Ensure collection exists
        store.ensure_collection_exists(collection)
        
        # Get count before deletion
        try:
            collection_info = client.get_collection(coll_name)
            count_before = collection_info.points_count
        except Exception as e:
            logger.warning(f"Could not get collection info: {e}")
            count_before = 0
        
        # Delete all points
        if count_before > 0:
            # Scroll through all points to get their IDs, then delete
            # This approach works reliably across Qdrant versions
            all_point_ids = []
            offset = None
            batch_size = 1000
            
            while True:
                points, next_offset = client.scroll(
                    collection_name=coll_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False
                )
                
                if not points:
                    break
                    
                all_point_ids.extend([p.id for p in points])
                
                if next_offset is None:
                    break
                offset = next_offset
            
            # Delete all points by IDs
            if all_point_ids:
                # Delete in batches to avoid overwhelming the API
                batch_size_delete = 1000
                for i in range(0, len(all_point_ids), batch_size_delete):
                    batch_ids = all_point_ids[i:i + batch_size_delete]
                    client.delete(
                        collection_name=coll_name,
                        points_selector=batch_ids
                    )
            
            logger.info(f"✅ delete_all completed: Deleted {count_before:,} points from {collection} collection")
        else:
            logger.info(f"✅ delete_all completed: Collection {collection} was already empty")
        
        elapsed = time.time() - start_time
        
        return _create_response(
            success=True,
            data={
                "collection": collection,
                "deleted_count": count_before,
                "message": f"Successfully deleted {count_before:,} vectors from {collection} collection"
            },
            metadata={
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "delete_all"
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ delete_all failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "delete_all"},
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
        
        # Try Qdrant filter first (fast, uses indexes)
        try:
            points, _ = store.cloud_client.scroll(
                collection_name=store.cloud_collection,
                scroll_filter=qdrant_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
        except (UnexpectedResponse, Exception) as e:
            # Fallback: If filter fails (e.g., unindexed field), scroll all and filter in Python
            error_msg = str(e)
            if "Index required" in error_msg or "Bad request" in error_msg or isinstance(e, UnexpectedResponse):
                logger.warning(f"Qdrant filter failed (likely unindexed field), falling back to Python filtering: {e}")
                # Scroll all points (with reasonable limit for fallback)
                scroll_limit = min(limit * 10, 10000)  # Get more points for filtering
                all_points, _ = store.cloud_client.scroll(
                    collection_name=store.cloud_collection,
                    limit=scroll_limit,
                    offset=0,
                    with_payload=True,
                    with_vectors=False
                )
                # Filter in Python
                points = store._filter_points_in_python(all_points, filter)
                # Apply pagination manually
                points = points[offset:offset + limit]
            else:
                # Re-raise if it's a different error
                raise
        
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


def index_repository(
    repository_path: str,
    index_docs: bool = True,
    index_code: bool = True,
    collection: str = "cloud",
    doc_patterns: Optional[List[str]] = None,
    code_patterns: Optional[List[str]] = None
) -> str:
    """
    Index/update entire repository into Qdrant.
    
    Automatically finds and indexes all documentation and code files.
    Handles incremental updates (only updates changed chunks).
    
    Args:
        repository_path: Path to repository directory (absolute or relative)
        index_docs: Whether to index documentation files
        index_code: Whether to index code files
        collection: Target collection ("cloud", "local", or "both")
        doc_patterns: Glob patterns for docs (default: ["**/*.md", "README.md"])
        code_patterns: Glob patterns for code (default: ["**/*.py", "**/*.ts", "**/*.js"])
    
    Returns:
        JSON response with indexing results
    """
    start_time = time.time()
    try:
        import os
        from pathlib import Path
        try:
            from ..indexing.indexer import index_all_documents, chunk_markdown
            from ..indexing.code_indexer import CodeIndexer
            from ..core.embedding_manager import EmbeddingManager
        except ImportError:
            import sys
            from pathlib import Path as PathLib
            sys.path.insert(0, str(PathLib(__file__).parent.parent.parent))
            from lib.indexing.indexer import index_all_documents, chunk_markdown
            from lib.indexing.code_indexer import CodeIndexer
            from lib.core.embedding_manager import EmbeddingManager
        
        # Validate repository path
        repo_path = Path(repository_path).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repository_path}")
        if not repo_path.is_dir():
            raise ValueError(f"Repository path must be a directory: {repository_path}")
        
        # Load config (will use existing .env for Qdrant)
        config = load_config()
        store = HybridVectorStore(config)
        
        # Override project_root temporarily
        original_project_root = config.project_root
        config.project_root = repo_path
        
        # Set default patterns if not provided
        if doc_patterns is None:
            doc_patterns = ["**/*.md", "README.md"]
        if code_patterns is None:
            code_patterns = ["**/*.py", "**/*.ts", "**/*.js", "**/*.tsx", "**/*.jsx"]
        
        # Override config patterns temporarily
        original_cloud_docs = config.cloud_docs
        original_code_paths = config.code_paths
        config.cloud_docs = doc_patterns
        config.code_paths = code_patterns
        
        # Determine collections
        # Default: cloud only (local storage is disabled by default)
        collections = []
        if collection == "cloud":
            collections = [collection]
        elif collection == "local":
            if not store.local_enabled:
                raise ValueError("Local storage is disabled. Cannot index to local collection. Enable it in config.local_qdrant.enabled")
            collections = [collection]
        elif collection == "both":
            # Only include local if it's enabled
            collections = ["cloud"]
            if store.local_enabled:
                collections.append("local")
            else:
                logger.warning("Local storage is disabled. Indexing to cloud only.")
        else:
            raise ValueError(f"Invalid collection: {collection}. Must be 'cloud', 'local', or 'both'")
        
        results = {
            "repository_path": str(repo_path),
            "collections": collections,
            "docs_indexed": 0,
            "code_indexed": 0,
            "errors": 0,
            "files_processed": [],
            "progress": {
                "status": "initializing",
                "stage": "starting",
                "docs_found": 0,
                "docs_processed": 0,
                "code_found": 0,
                "code_processed": 0,
                "current_file": None,
                "messages": []
            }
        }
        
        def add_progress_message(message: str, stage: str = None, print_to_stderr: bool = False):
            """Add progress message to results and optionally print to stderr for real-time visibility"""
            import sys  # Import sys in closure scope
            results["progress"]["messages"].append(message)
            if stage:
                results["progress"]["stage"] = stage
            # Use INFO level, not ERROR (progress messages are informational)
            logger.info(message)
            # Only print to stderr if explicitly requested (disabled by default to avoid cluttering Cursor logs)
            # Progress is still available in the response metadata
            if print_to_stderr:
                print(f"[PROGRESS] {message}", file=sys.stderr, flush=True)
        
        # Index documentation
        if index_docs:
            add_progress_message(f"🔍 Scanning for documentation files in: {repo_path}", "scanning_docs")
            try:
                # Count files first
                doc_files = []
                for pattern in doc_patterns:
                    for file_path in repo_path.glob(pattern):
                        if file_path.is_file() and file_path.suffix == '.md':
                            doc_files.append(file_path)
                
                results["progress"]["docs_found"] = len(doc_files)
                add_progress_message(f"📚 Found {len(doc_files)} documentation files to index", "indexing_docs")
                
                if doc_files:
                    add_progress_message(f"📝 Starting documentation indexing...", "indexing_docs")
                    doc_results = index_all_documents(store, config)
                    for coll in collections:
                        results["docs_indexed"] += doc_results.get(coll, 0)
                    results["errors"] += doc_results.get("errors", 0)
                    results["progress"]["docs_processed"] = len(doc_files)
                    add_progress_message(f"✅ Documentation indexing complete: {results['docs_indexed']} chunks indexed", "docs_complete")
                else:
                    add_progress_message("⚠️  No documentation files found matching patterns", "docs_complete")
            except Exception as e:
                logger.error(f"Document indexing failed: {e}", exc_info=True)
                results["errors"] += 1
                add_progress_message(f"❌ Document indexing failed: {str(e)}", "error")
        
        # Index code
        if index_code:
            add_progress_message(f"🔍 Scanning for code files in: {repo_path}", "scanning_code")
            try:
                embedder_mgr = EmbeddingManager(
                    doc_model=config.embedding_models.doc,
                    code_model=config.embedding_models.code
                )
                code_indexer = CodeIndexer(store, embedder_mgr)
                
                # Count files first
                code_files = []
                for code_pattern in code_patterns:
                    for code_file in repo_path.glob(code_pattern):
                        if code_file.is_file():
                            code_files.append(code_file)
                
                results["progress"]["code_found"] = len(code_files)
                add_progress_message(f"💻 Found {len(code_files)} code files to index", "indexing_code")
                
                if code_files:
                    add_progress_message(f"📝 Starting code indexing...", "indexing_code")
                    code_files_found = set()
                    processed_count = 0
                    
                    for idx, code_file in enumerate(code_files, 1):
                        rel_path = str(code_file.relative_to(repo_path))
                        code_files_found.add(rel_path)
                        results["progress"]["current_file"] = rel_path
                        add_progress_message(f"   [{idx}/{len(code_files)}] Indexing: {rel_path}", "indexing_code")
                        
                        try:
                            for coll in collections:
                                if code_indexer.index_file(str(code_file), coll):
                                    results["code_indexed"] += 1
                                    processed_count += 1
                                    results["files_processed"].append(rel_path)
                                else:
                                    results["errors"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to index {code_file}: {e}")
                            results["errors"] += 1
                            add_progress_message(f"   ⚠️  Failed to index {rel_path}: {str(e)}", "indexing_code")
                    
                    results["progress"]["code_processed"] = processed_count
                    results["progress"]["current_file"] = None
                    add_progress_message(f"✅ Code indexing complete: {processed_count} files indexed, {results['code_indexed']} chunks", "code_complete")
                else:
                    add_progress_message("⚠️  No code files found matching patterns", "code_complete")
            except Exception as e:
                logger.error(f"Code indexing failed: {e}", exc_info=True)
                results["errors"] += 1
                add_progress_message(f"❌ Code indexing failed: {str(e)}", "error")
        
        # Cleanup: Soft-delete chunks from files that no longer exist in repo
        add_progress_message("🧹 Cleaning up orphaned chunks (soft-delete)...", "cleanup")
        existing_files = set()
        
        # Collect all existing file paths from the repo
        if index_docs:
            for doc_pattern in doc_patterns:
                for file_path in repo_path.glob(doc_pattern):
                    if file_path.is_file() and file_path.suffix == '.md':
                        rel_path = str(file_path.relative_to(repo_path))
                        existing_files.add(rel_path.replace('\\', '/'))
        
        if index_code:
            for code_pattern in code_patterns:
                for file_path in repo_path.glob(code_pattern):
                    if file_path.is_file():
                        rel_path = str(file_path.relative_to(repo_path))
                        existing_files.add(rel_path.replace('\\', '/'))
        
        # Soft-delete orphaned chunks (chunks from files no longer in repo)
        cleanup_count = 0
        for collection in collections:
            # Skip cleanup for local if it's disabled
            if collection == "local" and not store.local_enabled:
                continue
            add_progress_message(f"   Cleaning {collection} collection...", "cleanup")
            cleaned = store.cleanup_deleted_files(existing_files, collection, dry_run=False)
            cleanup_count += cleaned
            if cleaned > 0:
                add_progress_message(f"   ✅ Marked {cleaned} orphaned chunks as deleted in {collection}", "cleanup")
        
        results["cleanup_deleted"] = cleanup_count
        if cleanup_count > 0:
            add_progress_message(f"✅ Cleanup complete: {cleanup_count} chunks marked as deleted", "cleanup_complete")
        else:
            add_progress_message("✅ Cleanup complete: No orphaned chunks found", "cleanup_complete")
        
        # Restore original config
        config.project_root = original_project_root
        config.cloud_docs = original_cloud_docs
        config.code_paths = original_code_paths
        
        # Get collection stats
        add_progress_message("📊 Getting collection statistics...", "finalizing")
        stats = store.get_collection_stats()
        
        elapsed = time.time() - start_time
        results["progress"]["status"] = "completed"
        results["progress"]["stage"] = "complete"
        
        total_chunks = results["docs_indexed"] + results["code_indexed"]
        add_progress_message(f"✅ Indexing complete! Total: {total_chunks} chunks indexed in {elapsed:.1f}s", "complete")
        add_progress_message(f"   📚 Docs: {results['docs_indexed']} chunks", "complete")
        add_progress_message(f"   💻 Code: {results['code_indexed']} chunks", "complete")
        add_progress_message(f"   📦 Collections: {', '.join(collections)}", "complete")
        
        logger.info(f"✅ index_repository completed in {elapsed:.2f}s: {results['docs_indexed']} docs, {results['code_indexed']} code files")
        
        return _create_response(
            success=True,
            data={
                **results,
                "collection_stats": stats,
                "total_indexed": total_chunks,
                "summary": {
                    "total_chunks": total_chunks,
                    "docs_chunks": results["docs_indexed"],
                    "code_chunks": results["code_indexed"],
                    "files_processed": len(results["files_processed"]),
                    "errors": results["errors"],
                    "cleanup_deleted": cleanup_count,
                    "elapsed_seconds": round(elapsed, 2)
                }
            },
            metadata={
                "timing_ms": round(elapsed * 1000, 2),
                "operation": "index_repository",
                "progress": results["progress"]
            },
            errors=[]
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ index_repository failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return _create_response(
            success=False,
            data=None,
            metadata={"timing_ms": round(elapsed * 1000, 2), "operation": "index_repository"},
            errors=[_format_error(e)]
        )


# MCP Tool Definitions

add_vector_tool_mcp = Tool(
    name="add_vector",
    description="Store new data (text/code/log) with embeddings + metadata. Auto-embeds content if vector not provided. Returns generated vector ID as string (to prevent JavaScript precision loss for large integers).",
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
    description="Retrieve a stored vector item by ID. Returns vector data with metadata. Note: vector_id is returned as string to prevent JavaScript precision loss.",
    inputSchema={
        "type": "object",
        "properties": {
            "vector_id": {
                "oneOf": [
                    {"type": "integer"},
                    {"type": "string", "description": "Vector ID as string (handles large integers safely)"}
                ],
                "description": "Vector ID to retrieve (accepts int or string - string recommended for large IDs)"
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
    description="Update text/metadata for an existing vector entry. Merges metadata with existing. Re-embeds if content changes. Note: vector_id is returned as string to prevent JavaScript precision loss.",
    inputSchema={
        "type": "object",
        "properties": {
            "vector_id": {
                "oneOf": [
                    {"type": "integer"},
                    {"type": "string", "description": "Vector ID as string (handles large integers safely)"}
                ],
                "description": "Vector ID to update (accepts int or string - string recommended for large IDs)"
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
    description="Delete a stored vector entry. Supports soft-delete (mark as deleted) and hard-delete (permanent removal). Note: vector_id is returned as string to prevent JavaScript precision loss.",
    inputSchema={
        "type": "object",
        "properties": {
            "vector_id": {
                "oneOf": [
                    {"type": "integer"},
                    {"type": "string", "description": "Vector ID as string (handles large integers safely)"}
                ],
                "description": "Vector ID to delete (accepts int or string - string recommended for large IDs)"
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

index_repository_tool_mcp = Tool(
    name="index_repository",
    description="Index/update entire repository into Qdrant. Automatically finds and indexes all documentation and code files. Handles incremental updates.",
    inputSchema={
        "type": "object",
        "properties": {
            "repository_path": {
                "type": "string",
                "description": "Path to repository directory to index (absolute or relative)"
            },
            "index_docs": {
                "type": "boolean",
                "description": "Index documentation files (.md)",
                "default": True
            },
            "index_code": {
                "type": "boolean",
                "description": "Index code files (.py, .ts, .js, etc.)",
                "default": True
            },
            "collection": {
                "type": "string",
                "description": "Target collection: 'cloud', 'local', or 'both'",
                "enum": ["cloud", "local", "both"],
                "default": "cloud"
            },
            "doc_patterns": {
                "type": "array",
                "description": "Glob patterns for documentation files (default: ['**/*.md', 'README.md'])",
                "items": {"type": "string"},
                "default": ["**/*.md", "README.md"]
            },
            "code_patterns": {
                "type": "array",
                "description": "Glob patterns for code files (default: ['**/*.py', '**/*.ts', '**/*.js'])",
                "items": {"type": "string"},
                "default": ["**/*.py", "**/*.ts", "**/*.js"]
            }
        },
        "required": ["repository_path"]
    }
)

delete_all_tool_mcp = Tool(
    name="delete_all",
    description="⚠️  WARNING: Delete ALL vectors from a collection. This permanently deletes ALL indexed data! Requires confirm=True for safety.",
    inputSchema={
        "type": "object",
        "properties": {
            "collection": {
                "type": "string",
                "description": "Target collection: 'cloud' or 'local'",
                "enum": ["cloud", "local"],
                "default": "cloud"
            },
            "confirm": {
                "type": "boolean",
                "description": "Must be True to actually delete (safety check). This operation cannot be undone!",
                "default": False
            }
        },
        "required": ["confirm"]
    }
)
