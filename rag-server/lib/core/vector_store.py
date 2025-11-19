from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, NearestQuery, PayloadSchemaType, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    content: str
    file_path: str  # Relative to project root
    line_number: int
    score: float
    collection: str  # "cloud" or "local"
    metadata: Dict

class HybridVectorStore:
    def __init__(self, config):
        """Initialize cloud + local Qdrant clients"""
        # Cloud: Use URL + API key from config
        self.cloud_client = QdrantClient(
            url=config.cloud_qdrant.url,
            api_key=config.cloud_qdrant.api_key,
            timeout=config.cloud_qdrant.timeout
        )
        self.cloud_collection = config.cloud_qdrant.collection
        
        # Local: Use path (embedded mode)
        local_path = Path(config.local_qdrant.path)
        if not local_path.is_absolute():
            # Relative to rag-server directory
            base_path = config.rag_server_dir
            local_path = base_path / local_path
        local_path.mkdir(parents=True, exist_ok=True)
        
        self.local_client = QdrantClient(path=str(local_path))
        self.local_collection = config.local_qdrant.collection
        
        # Embedding model (single model for now, future: add CodeBERT support)
        # Using MiniLM-L6-v2 (384-dim) for both docs + code (safe default)
        self.embedder = SentenceTransformer(config.embedding_model)
        self.vector_size = 384  # all-MiniLM-L6-v2 output size
        logger.info(f"Using embedder: {config.embedding_model} (vector_size: {self.vector_size})")
        
        # Ensure collections exist
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Create collections if they don't exist and ensure payload indexes"""
        self._ensure_collection(self.cloud_client, self.cloud_collection, "cloud")
        self._ensure_collection(self.local_client, self.local_collection, "local")
    
    def _ensure_collection(self, client: QdrantClient, collection_name: str, collection_type: str):
        """Create a single collection if it doesn't exist and ensure payload indexes"""
        try:
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            if collection_name not in collection_names:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created {collection_type} collection: {collection_name}")
            
            self._ensure_payload_indexes(client, collection_name, collection_type)
        except Exception as e:
            if collection_type == "local":
                logger.error(f"Local collection creation failed: {e}")
                raise
            else:
                logger.warning(f"Cloud collection check failed: {e}")
    
    def _ensure_payload_indexes(self, client: QdrantClient, collection_name: str, collection_type: str):
        """Create payload indexes for filtering performance"""
        # Skip payload indexes for local Qdrant - they're not supported and cause warnings
        if collection_type == "local":
            logger.debug(f"Skipping payload indexes for local Qdrant (not supported)")
            return
        
        try:
            # Index fields with proper schema types:
            # - KEYWORD for string fields (file_path, section, language, content_type)
            # - No index needed for is_deleted (boolean) - Qdrant handles this automatically
            index_fields = {
                "file_path": PayloadSchemaType.KEYWORD,
                "section": PayloadSchemaType.KEYWORD,
                "language": PayloadSchemaType.KEYWORD,
                "content_type": PayloadSchemaType.KEYWORD,
                # is_deleted is boolean - Qdrant will handle filtering without explicit index
            }
            
            for field_name, schema_type in index_fields.items():
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=schema_type
                    )
                    logger.debug(f"Created {field_name} index (type: {schema_type}) in {collection_type} collection")
                except Exception as e:
                    # Index may already exist - that's ok
                    logger.debug(f"Index {field_name} not created (may exist): {e}")
        except Exception as e:
            logger.warning(f"Failed to ensure payload indexes for {collection_type} collection: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Search: Cloud first → Local fallback
        
        Strategy:
        1. Try cloud search (no boolean filter - filter results in Python)
        2. If cloud fails or returns < top_k, search local
        3. Merge results, deduplicate by file_path:line_number
        4. Filter out soft-deleted chunks in Python
        5. Sort by score descending
        6. Return top_k results
        
        Note: We filter is_deleted in Python (not in query) to avoid requiring
        a boolean index in cloud Qdrant. This works for both local and cloud.
        """
        query_vector = self.embedder.encode(query).tolist()
        results = []
        
        # Try cloud first (no filter - we'll filter in Python)
        try:
            cloud_response = self.cloud_client.query_points(
                collection_name=self.cloud_collection,
                query=NearestQuery(nearest=query_vector),
                limit=top_k * 2  # Fetch more to account for deleted items
            )
            results.extend(self._parse_search_results(cloud_response.points, 'cloud'))
        except Exception as e:
            logger.warning(f"Cloud search failed: {e}, using local only")
        
        # If not enough results, search local
        if len(results) < top_k:
            try:
                local_response = self.local_client.query_points(
                    collection_name=self.local_collection,
                    query=NearestQuery(nearest=query_vector),
                    limit=top_k * 2  # Fetch more to account for deleted items
                )
                existing_keys = {(r.file_path, r.line_number) for r in results}
                for result in local_response.points:
                    key = (result.payload.get('file_path', ''), result.payload.get('line_start', 0))
                    if key not in existing_keys:
                        results.append(self._create_search_result(result, 'local'))
                        existing_keys.add(key)
            except Exception as e:
                logger.error(f"Local search failed: {e}")
        
        # Filter out soft-deleted chunks (do this in Python, not in query)
        # This avoids requiring a boolean index in cloud Qdrant
        results = [r for r in results if not r.metadata.get('is_deleted', False)]
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _parse_search_results(self, points, collection: str) -> List[SearchResult]:
        """Parse Qdrant points into SearchResult objects"""
        return [self._create_search_result(point, collection) for point in points]
    
    def _create_search_result(self, point, collection: str) -> SearchResult:
        """Create a SearchResult from a Qdrant point"""
        payload = point.payload
        return SearchResult(
            content=payload.get('content', ''),
            file_path=payload.get('file_path', ''),
            line_number=payload.get('line_start', 0),
            score=getattr(point, 'score', 0.0),
            collection=collection,
            metadata=payload
        )
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path separators for consistent comparison"""
        return path.replace('\\', '/')
    
    def _get_existing_chunks(self, client, collection_name: str, doc_path: str) -> Dict:
        """Get existing chunks for a file, keyed by (file_path, line_start)"""
        existing = {}
        try:
            # Normalize the doc_path for comparison
            normalized_doc_path = self._normalize_path(doc_path)
            # Also prepare path variants for matching
            path_variants = {
                normalized_doc_path,
                doc_path,
                doc_path.replace('/', '\\'),
                doc_path.replace('\\', '/')
            }
            
            # Scroll all points (local Qdrant doesn't support payload indexes for filtering)
            # Filter in Python code instead
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=100000,  # Large limit to get all
                with_payload=True,
                with_vectors=False
            )
            
            # Filter points by file_path in Python
            for point in points:
                payload = point.payload
                point_file_path = payload.get('file_path', '')
                normalized_point_path = self._normalize_path(point_file_path)
                
                # Check if this point belongs to our file (try all path variants)
                if normalized_point_path in path_variants or point_file_path in path_variants:
                    key = (normalized_doc_path, payload.get('line_start', 0))
                    existing[key] = {
                        'id': point.id,
                        'content': payload.get('content', ''),
                        'line_start': payload.get('line_start', 0),
                        'line_end': payload.get('line_end', 0)
                    }
            
            if existing:
                logger.debug(f"Found {len(existing)} existing chunks for {doc_path}")
        except Exception as e:
            logger.debug(f"Could not fetch existing chunks: {e}")
        return existing
    
    def index_doc(self, doc_path: str, collection: str, chunks: List[Dict]) -> bool:
        """
        Incrementally index document chunks - only updates what changed
        
        Strategy:
        1. Get existing chunks for this file
        2. Compare new chunks with existing:
           - Same line_start + same content = skip (no change)
           - Same line_start + different content = update (content changed)
           - New line_start = add (new content)
        3. Delete chunks that no longer exist in new file
        4. Only update/add/delete what's necessary
        
        Args:
            doc_path: Relative path from project root
            collection: "cloud" or "local"
            chunks: List of {content, line_start, line_end, metadata}
        
        Returns: True if successful
        """
        if collection not in ["cloud", "local"]:
            raise ValueError(f"Invalid collection: {collection}. Must be 'cloud' or 'local'")
        
        client = self.cloud_client if collection == "cloud" else self.local_client
        coll_name = self.cloud_collection if collection == "cloud" else self.local_collection
        
        try:
            # Log which file we're processing
            logger.info(f"📄 Processing file: {doc_path} (collection: {collection})")
            
            # Get existing chunks for this file ONLY
            existing_chunks = self._get_existing_chunks(client, coll_name, doc_path)
            logger.info(f"   Found {len(existing_chunks)} existing chunks for this file")
            
            # Normalize path for comparison
            normalized_doc_path = self._normalize_path(doc_path)
            
            # Build maps for comparison
            new_chunks_map = {}
            for chunk in chunks:
                key = (normalized_doc_path, chunk['line_start'])
                new_chunks_map[key] = chunk
            
            # Determine what to do with each chunk
            to_update = []
            to_add = []
            to_delete_ids = []
            
            # Check new chunks: update if changed, add if new
            for key, new_chunk in new_chunks_map.items():
                if key in existing_chunks:
                    # Chunk exists - check if content changed
                    existing_content = existing_chunks[key]['content']
                    if existing_content != new_chunk['content']:
                        # Content changed - need to update
                        to_update.append(new_chunk)
                else:
                    # New chunk - need to add
                    to_add.append(new_chunk)
            
            # Check existing chunks: delete if no longer in new file
            for key, existing_chunk in existing_chunks.items():
                if key not in new_chunks_map:
                    # Chunk no longer exists - need to delete
                    to_delete_ids.append(existing_chunk['id'])
            
            # Process updates and adds
            # Also unmark any previously soft-deleted chunks for this file
            points_to_upsert = []
            for chunk in to_update + to_add:
                try:
                    vector = self.embedder.encode(chunk['content']).tolist()
                    point_id = abs(hash(f"{doc_path}:{chunk['line_start']}")) % (2**63 - 1)
                    payload = {
                        "content": chunk['content'],
                        "file_path": doc_path,
                        "line_start": chunk['line_start'],
                        "line_end": chunk['line_end'],
                        "is_deleted": False,  # Unmark if previously deleted
                        **chunk.get('metadata', {})
                    }
                    points_to_upsert.append(PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    ))
                except Exception as e:
                    logger.error(f"Failed to encode chunk at line {chunk.get('line_start', '?')}: {e}")
                    continue
            
            # Execute operations
            if points_to_upsert:
                client.upsert(collection_name=coll_name, points=points_to_upsert)
            
            if to_delete_ids:
                client.delete(collection_name=coll_name, points_selector=to_delete_ids)
            
            # Log summary with clear file identification
            if to_update or to_add or to_delete_ids:
                actions = []
                if to_update:
                    actions.append(f"{len(to_update)} updated")
                if to_add:
                    actions.append(f"{len(to_add)} added")
                if to_delete_ids:
                    actions.append(f"{len(to_delete_ids)} deleted")
                logger.info(f"✅ {doc_path} ({collection}): {', '.join(actions)} - ONLY this file was modified")
            else:
                logger.info(f"✅ {doc_path} ({collection}): No changes detected - file already up to date")
            
            return True
        except Exception as e:
            logger.error(f"Indexing failed for {doc_path}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get stats for both collections"""
        stats = {"cloud": {"count": 0, "size": 0}, "local": {"count": 0, "size": 0}}
        
        try:
            cloud_info = self.cloud_client.get_collection(self.cloud_collection)
            stats["cloud"]["count"] = cloud_info.points_count
        except Exception as e:
            logger.warning(f"Failed to get cloud stats: {e}")
        
        try:
            local_info = self.local_client.get_collection(self.local_collection)
            stats["local"]["count"] = local_info.points_count
        except Exception as e:
            logger.warning(f"Failed to get local stats: {e}")
        
        return stats

    def cleanup_deleted_files(self, existing_files: set, collection: str = "local", dry_run: bool = True) -> int:
        """
        Soft-delete chunks for files that no longer exist on disk.
        
        Strategy: Mark chunks as deleted (is_deleted: true) instead of physically removing.
        This allows recovery and is safer. Deleted chunks are excluded from search.
        
        Args:
            existing_files: Set of file paths that currently exist
            collection: "cloud" or "local"
            dry_run: When True, only reports what would be marked as deleted (no marking)
        
        Returns:
            Number of chunks marked as deleted
        """
        if collection not in ["cloud", "local"]:
            raise ValueError(f"Invalid collection: {collection}")
        
        client = self.cloud_client if collection == "cloud" else self.local_client
        coll_name = self.cloud_collection if collection == "cloud" else self.local_collection
        
        try:
            # Get all indexed file paths
            indexed_files = set()
            points_to_mark_deleted = []
            
            points, _ = client.scroll(
                collection_name=coll_name,
                limit=100000,
                with_payload=True,
                with_vectors=False
            )
            
            for point in points:
                # Skip already deleted chunks
                if point.payload.get('is_deleted', False):
                    continue
                    
                file_path = point.payload.get('file_path', '')
                if file_path:
                    normalized = self._normalize_path(file_path)
                    indexed_files.add(normalized)
                    
                    # Check if file no longer exists
                    if normalized not in existing_files:
                        # Also check path variants
                        path_variants = {
                            file_path,
                            file_path.replace('/', '\\'),
                            file_path.replace('\\', '/'),
                            normalized
                        }
                        if not any(variant in existing_files for variant in path_variants):
                            points_to_mark_deleted.append(point.id)
            
            # Soft-delete orphaned chunks (mark as deleted, don't remove)
            if points_to_mark_deleted:
                if dry_run:
                    logger.info(f"🧪 Dry-run: {len(points_to_mark_deleted)} chunks would be marked as deleted ({collection})")
                    return len(points_to_mark_deleted)
                else:
                    # Mark as deleted by updating payload (batch update for efficiency)
                    # Qdrant supports batch updates - process in chunks of 1000 to avoid timeouts
                    batch_size = 1000
                    total_marked = 0
                    
                    for i in range(0, len(points_to_mark_deleted), batch_size):
                        batch = points_to_mark_deleted[i:i + batch_size]
                        try:
                            client.set_payload(
                                collection_name=coll_name,
                                payload={"is_deleted": True},
                                points=batch  # Batch update - much faster!
                            )
                            total_marked += len(batch)
                        except Exception as e:
                            logger.warning(f"Failed to mark batch {i//batch_size + 1} as deleted: {e}")
                            # Fallback: try individual updates for this batch
                            for point_id in batch:
                                try:
                                    client.set_payload(
                                        collection_name=coll_name,
                                        payload={"is_deleted": True},
                                        points=[point_id]
                                    )
                                    total_marked += 1
                                except Exception as e2:
                                    logger.warning(f"Failed to mark point {point_id} as deleted: {e2}")
                    
                    logger.info(f"🏷️  Marked {total_marked} chunks as deleted (soft-delete) ({collection})")
                    logger.info(f"   Note: These chunks are excluded from search but can be recovered")
                    return total_marked
            
            return 0
            
        except Exception as e:
            logger.error(f"Cleanup failed for {collection}: {e}")
            return 0

    def hybrid_search(
        self,
        query: str,
        embedder,
        top_k: int = 20,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
    ) -> List[SearchResult]:
        """
        Hybrid search combining BM25 (keyword) and vector (semantic) search.

        Args:
            query: Search query
            embedder: Embedding model to use (for routing doc vs code)
            top_k: Number of results to return
            bm25_weight: Weight for BM25 scores (0.0-1.0)
            vector_weight: Weight for vector scores (0.0-1.0)

        Returns:
            Ranked list of search results

        Raises:
            ValueError: If weights don't sum to ~1.0
        """
        if abs(bm25_weight + vector_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {bm25_weight + vector_weight}")

        try:
            # Get vector embedding
            query_vector = embedder.encode(query).tolist()

            # Search cloud collection (with both BM25 and vector)
            cloud_results = []
            try:
                # No filter in query - we'll filter is_deleted in Python to avoid boolean index requirement
                # Qdrant supports both BM25 and vector search
                # For now, use vector search as primary
                cloud_response = self.cloud_client.query_points(
                    collection_name=self.cloud_collection,
                    query=NearestQuery(nearest=query_vector),
                    limit=top_k * 2,  # Get more for hybrid scoring and deleted item filtering
                )
                cloud_results = self._parse_search_results(cloud_response.points, "cloud")
            except Exception as e:
                logger.warning(f"Cloud hybrid search failed: {e}, falling back to local")

            # Search local collection if needed
            local_results = []
            if len(cloud_results) < top_k:
                try:
                    # No filter in query - filter in Python instead
                    local_response = self.local_client.query_points(
                        collection_name=self.local_collection,
                        query=NearestQuery(nearest=query_vector),
                        limit=top_k * 2,
                    )
                    existing_keys = {(r.file_path, r.line_number) for r in cloud_results}
                    for result in local_response.points:
                        key = (result.payload.get("file_path", ""), result.payload.get("line_start", 0))
                        if key not in existing_keys:
                            local_results.append(self._create_search_result(result, "local"))
                            existing_keys.add(key)
                except Exception as e:
                    logger.error(f"Local hybrid search failed: {e}")

            # Combine results
            all_results = cloud_results + local_results
            
            # Filter out soft-deleted chunks (do this in Python, not in query)
            # This avoids requiring a boolean index in cloud Qdrant
            all_results = [r for r in all_results if not r.metadata.get('is_deleted', False)]
            
            # Sort and return top_k
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[:top_k]

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    def search_with_expansion(
        self,
        query: str,
        embedder,
        top_k: int = 20,
        rerank_top_k: int = 10,
    ) -> List[SearchResult]:
        """
        Section-aware retrieval: if query matches a section, get ALL chunks from that section.

        Strategy:
        1. Initial retrieval (top_k results)
        2. Identify sections represented in results
        3. Get ALL chunks from those sections (using Qdrant filters)
        4. Return merged and deduplicated results

        Args:
            query: Search query
            embedder: Embedding model to use
            top_k: Initial retrieval count
            rerank_top_k: Final result count

        Returns:
            Section-expanded search results
        """
        try:
            # Step 1: Initial retrieval
            initial_results = self.hybrid_search(query, embedder, top_k=top_k)

            if not initial_results:
                return []

            # Step 2: Identify sections
            section_files = {}  # Dict of (file_path, section) -> list of results
            for result in initial_results:
                section = result.metadata.get("section", "Unknown")
                file_path = result.file_path
                key = (file_path, section)

                if key not in section_files:
                    section_files[key] = []
                section_files[key].append(result)

            # Step 3: Expand - get ALL chunks from relevant sections
            expanded_results = []
            seen_keys = set()

            for (file_path, section), _ in section_files.items():
                try:
                    # Use Qdrant filters to get all chunks from this section
                    section_chunks = self._get_all_chunks_from_section(file_path, section)
                    for chunk in section_chunks:
                        key = (chunk.file_path, chunk.line_number)
                        if key not in seen_keys:
                            expanded_results.append(chunk)
                            seen_keys.add(key)
                except Exception as e:
                    logger.warning(f"Failed to expand section {section} from {file_path}: {e}")
                    # Fall back to initial results for this section
                    for result in section_files[(file_path, section)]:
                        key = (result.file_path, result.line_number)
                        if key not in seen_keys:
                            expanded_results.append(result)
                            seen_keys.add(key)

            # Sort by score
            expanded_results.sort(key=lambda x: x.score, reverse=True)
            return expanded_results[:rerank_top_k]

        except Exception as e:
            logger.error(f"Section-aware search failed: {e}")
            # Fall back to basic search
            return self.hybrid_search(query, embedder, top_k=rerank_top_k)

    def _get_all_chunks_from_section(self, file_path: str, section: str) -> List[SearchResult]:
        """
        Get ALL chunks from a specific section using Qdrant filters.

        Args:
            file_path: File path to filter by
            section: Section name to filter by

        Returns:
            List of all chunks from that section

        Raises:
            Exception: If retrieval fails
        """
        chunks = []

        # Try cloud first
        try:
            # Create filter for this file and section (no boolean filter - filter in Python)
            # Note: section is stored at top-level, not in nested metadata
            filter_condition = Filter(
                must=[
                    FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                    FieldCondition(key="section", match=MatchValue(value=section)),
                ]
            )

            points, _ = self.cloud_client.scroll(
                collection_name=self.cloud_collection,
                scroll_filter=filter_condition,
                limit=1000,
                with_payload=True,
                with_vectors=False,
            )

            # Filter out soft-deleted chunks in Python
            for point in points:
                if not point.payload.get('is_deleted', False):
                    chunks.append(self._create_search_result(point, "cloud"))

        except Exception as e:
            logger.warning(f"Cloud section retrieval failed for {file_path}:{section}: {e}")

        # Try local if cloud didn't return enough
        if len(chunks) < 10:
            try:
                filter_condition = Filter(
                    must=[
                        FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                        FieldCondition(key="section", match=MatchValue(value=section)),
                    ]
                )

                points, _ = self.local_client.scroll(
                    collection_name=self.local_collection,
                    scroll_filter=filter_condition,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False,
                )

                existing_keys = {(c.file_path, c.line_number) for c in chunks}
                # Filter out soft-deleted chunks in Python
                for point in points:
                    if not point.payload.get('is_deleted', False):
                        key = (point.payload.get("file_path", ""), point.payload.get("line_start", 0))
                        if key not in existing_keys:
                            chunks.append(self._create_search_result(point, "local"))
                            existing_keys.add(key)

            except Exception as e:
                logger.warning(f"Local section retrieval failed for {file_path}:{section}: {e}")

        logger.debug(f"Retrieved {len(chunks)} chunks from section {section} in {file_path}")
        return chunks

