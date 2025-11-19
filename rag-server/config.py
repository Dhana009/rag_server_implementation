import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class CloudQdrantConfig(BaseModel):
    url: str
    api_key: str
    collection: str
    timeout: int = 30
    retry_attempts: int = 3

class LocalQdrantConfig(BaseModel):
    path: str
    collection: str
    recreate_if_exists: bool = False

class EmbeddingModelsConfig(BaseModel):
    """Embedding models configuration - separate models for docs and code"""
    doc: str = "sentence-transformers/all-MiniLM-L6-v2"
    code: str = "microsoft/codebert-base"
    reranking: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

class HybridRetrievalConfig(BaseModel):
    """Hybrid retrieval settings - BM25 + Vector"""
    search_top_k: int = 20  # Initial retrieval
    rerank_top_k: int = 10  # After reranking
    max_results: int = 25   # Final results
    hybrid_weights: Dict[str, float] = {"bm25": 0.3, "vector": 0.7}

class ChunkingConfig(BaseModel):
    """Chunking strategy for docs and code"""
    doc_chunk_size: int = 1000
    doc_chunk_overlap: int = 100
    code_chunk_strategy: str = "function_level"
    code_chunk_overlap: int = 50

class Config(BaseModel):
    cloud_qdrant: CloudQdrantConfig
    local_qdrant: LocalQdrantConfig
    cloud_docs: list[str]
    local_docs: list[str]
    decision_log_path: str
    
    # Backward compatibility: keep embedding_model for legacy code
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 500  # Backward compat
    chunk_overlap: int = 50  # Backward compat
    search_top_k: int = 5  # Backward compat
    max_results: int = 10  # Backward compat
    
    # New: Enhanced configuration
    embedding_models: EmbeddingModelsConfig = EmbeddingModelsConfig()
    hybrid_retrieval: HybridRetrievalConfig = HybridRetrievalConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    code_paths: list[str] = []
    exclude_patterns: list[str] = [
        "**/node_modules/**",
        "**/__pycache__/**",
        "**/.next/**",
        "**/dist/**",
        "**/build/**"
    ]
    
    # Runtime configuration (not from JSON)
    project_root: Optional[Path] = None  # Will be set during load_config
    rag_server_dir: Optional[Path] = None  # Will be set during load_config

def _find_config_file(start_path: Path) -> Path:
    """
    Find mcp-config.json - check in rag-server/ first, then search upward
    
    Args:
        start_path: Starting directory (rag-server/)
        
    Returns:
        Path to mcp-config.json file
        
    Raises:
        FileNotFoundError: If mcp-config.json not found
    """
    # First, check in rag-server/ directory
    config_in_server = start_path / "mcp-config.json"
    if config_in_server.exists():
        return config_in_server
    
    # Check in rag-server/config/ directory
    config_in_config = start_path / "config" / "mcp-config.json"
    if config_in_config.exists():
        return config_in_config
    
    # Fallback: search upward (for backward compatibility)
    current = start_path.resolve()
    while current != current.parent:
        config_file = current / "mcp-config.json"
        if config_file.exists():
            return config_file
        current = current.parent
    
    # Last fallback: current working directory
    cwd = Path.cwd()
    if (cwd / "mcp-config.json").exists():
        return cwd / "mcp-config.json"
    
    raise FileNotFoundError(
        f"Could not find mcp-config.json. Checked: {start_path}/mcp-config.json, "
        f"{start_path}/config/mcp-config.json, and searched upward from {start_path}. "
        f"Please set MCP_CONFIG_FILE environment variable or create mcp-config.json in rag-server/ directory."
    )


def load_config() -> Config:
    """
    Load configuration from mcp-config.json and .env file
    
    Qdrant credentials are ALWAYS loaded from .env file (rag-server/.env)
    Project settings (paths, models, etc.) are loaded from mcp-config.json
    
    Configuration paths can be set via environment variables:
    - MCP_PROJECT_ROOT: Root directory where mcp-config.json is located (default: auto-detect)
    - MCP_CONFIG_FILE: Full path to config JSON (default: {PROJECT_ROOT}/mcp-config.json)
    - MCP_ENV_FILE: Full path to .env file (default: {RAG_SERVER_DIR}/.env)
    
    Returns: Validated Config object with project_root and rag_server_dir set
    
    Raises:
        FileNotFoundError: If config files missing (with exact path)
        ValueError: If env vars missing (with exact var name)
        ValidationError: If config invalid (with field names)
    """
    # 1. Determine rag-server directory (where this file is located)
    rag_server_dir = Path(__file__).parent.resolve()
    
    # 2. Load .env file FIRST (for Qdrant credentials)
    env_file = os.getenv("MCP_ENV_FILE")
    if env_file:
        env_path = Path(env_file).resolve()
    else:
        env_path = rag_server_dir / ".env"
    
    if not env_path.exists():
        raise FileNotFoundError(
            f"Missing .env file at {env_path}\n"
            f"Create .env file with:\n"
            f"  QDRANT_CLOUD_URL=https://your-cluster.qdrant.io:6333\n"
            f"  QDRANT_API_KEY=your-api-key-here\n"
            f"  QDRANT_COLLECTION=mcp-rag\n"
            f"\nOr set MCP_ENV_FILE environment variable to point to your .env file."
        )
    
    # Load environment variables from .env file
    load_dotenv(env_path)
    
    # Get Qdrant credentials from environment
    qdrant_url = os.getenv("QDRANT_CLOUD_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "mcp-rag")
    
    if not qdrant_url or not qdrant_api_key:
        missing = []
        if not qdrant_url:
            missing.append("QDRANT_CLOUD_URL")
        if not qdrant_api_key:
            missing.append("QDRANT_API_KEY")
        raise ValueError(
            f"Missing required environment variables in {env_path}: {', '.join(missing)}\n"
            f"Add them to your .env file:\n"
            f"  QDRANT_CLOUD_URL=https://your-cluster.qdrant.io:6333\n"
            f"  QDRANT_API_KEY=your-api-key-here\n"
            f"  QDRANT_COLLECTION=mcp-rag  (optional, defaults to 'mcp-rag')"
        )
    
    # 3. Find and load mcp-config.json (for project settings)
    config_file = os.getenv("MCP_CONFIG_FILE")
    if config_file:
        config_path = Path(config_file).resolve()
    else:
        config_path = _find_config_file(rag_server_dir)
    
    # 4. Determine project root
    project_root = os.getenv("MCP_PROJECT_ROOT")
    if project_root:
        project_root = Path(project_root).resolve()
        if not project_root.exists():
            raise FileNotFoundError(f"MCP_PROJECT_ROOT points to non-existent directory: {project_root}")
    else:
        # Default: parent of rag-server/ (one level up)
        # This can be overridden in config file with "project_root" field
        project_root = rag_server_dir.parent.resolve()
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing mcp-config.json at {config_path}. "
            f"Set MCP_CONFIG_FILE or create mcp-config.json in rag-server/ directory."
        )
    
    # 5. Load project config JSON
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # Override project_root if specified in config
    if "project_root" in config_data:
        project_root_from_config = Path(config_data["project_root"])
        if not project_root_from_config.is_absolute():
            # Relative to config file location
            project_root = (config_path.parent / project_root_from_config).resolve()
        else:
            project_root = project_root_from_config.resolve()
        if not project_root.exists():
            raise FileNotFoundError(f"project_root in config points to non-existent directory: {project_root}")
    
    # 6. Merge Qdrant config from .env with project config
    # Remove cloud_qdrant from config_data if it exists (we use .env instead)
    if "cloud_qdrant" in config_data:
        logger.warning("cloud_qdrant in mcp-config.json is ignored. Using values from .env file instead.")
        del config_data["cloud_qdrant"]
    
    # Add Qdrant config from .env
    config_data["cloud_qdrant"] = {
        "url": qdrant_url,
        "api_key": qdrant_api_key,
        "collection": qdrant_collection,
        "timeout": 30,
        "retry_attempts": 3
    }
    
    # 7. Validate and create Config object
    try:
        config = Config(**config_data)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            error_details.append(f"  {field}: {error['msg']}")
        raise ValidationError(
            f"Invalid configuration in {config_path}:\n" + "\n".join(error_details)
        ) from e
    
    # 8. Set runtime paths
    config.project_root = project_root
    config.rag_server_dir = rag_server_dir
    
    logger.info(f"✅ Config loaded: project_root={project_root}, qdrant_collection={qdrant_collection}")
    
    return config
