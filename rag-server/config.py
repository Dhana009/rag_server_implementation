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
    rag_server_dir: Optional[Path] = None  # Will be set during load_config (renamed from mcp_server_dir for clarity)

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
    Load configuration from mcp-config.json and .env.qdrant
    
    Configuration paths can be set via environment variables:
    - MCP_PROJECT_ROOT: Root directory where mcp-config.json is located (default: auto-detect)
    - MCP_CONFIG_FILE: Full path to config JSON (default: {PROJECT_ROOT}/mcp-config.json)
    - MCP_ENV_FILE: Full path to .env.qdrant (default: {MCP_SERVER_DIR}/.env.qdrant)
    
    Returns: Validated Config object with project_root and rag_server_dir set
    
    Raises:
        FileNotFoundError: If config files missing (with exact path)
        ValueError: If env vars missing (with exact var name)
        ValidationError: If config invalid (with field names)
    """
    # 1. Determine rag-server directory (where this file is located)
    rag_server_dir = Path(__file__).parent.resolve()
    
    # 2. Find config file (prefer rag-server/ directory)
    config_file = os.getenv("MCP_CONFIG_FILE")
    if config_file:
        config_path = Path(config_file).resolve()
    else:
        config_path = _find_config_file(rag_server_dir)
    
    # 3. Determine project root
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
    
    # 4. Load project config JSON first (to get project_root if specified)
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
    
    # 5. Load Qdrant configuration (try qdrant.config.json first, then .env.qdrant)
    # Check in rag-server dir first, then config/ folder
    qdrant_config_path = rag_server_dir / "qdrant.config.json"
    if not qdrant_config_path.exists():
        qdrant_config_path = rag_server_dir / "config" / "qdrant.config.json"
    env_file = os.getenv("MCP_ENV_FILE")
    if env_file:
        env_path = Path(env_file).resolve()
    else:
        env_path = rag_server_dir / ".env.qdrant"
    
    qdrant_url = None
    qdrant_api_key = None
    
    # Try qdrant.config.json first (simpler, direct config)
    if qdrant_config_path.exists():
        try:
            with open(qdrant_config_path, 'r', encoding='utf-8') as f:
                qdrant_config = json.load(f)
            qdrant_url = qdrant_config.get("url")
            qdrant_api_key = qdrant_config.get("api_key")
            if qdrant_url and qdrant_api_key:
                os.environ["QDRANT_CLOUD_URL"] = qdrant_url
                os.environ["QDRANT_API_KEY"] = qdrant_api_key
        except Exception as e:
            logger.warning(f"Failed to load qdrant.config.json: {e}")
    
    # Fallback to .env.qdrant if qdrant.config.json not found or incomplete
    if not qdrant_url or not qdrant_api_key:
        if env_path.exists():
            load_dotenv(env_path)
        else:
            raise FileNotFoundError(
                f"Missing Qdrant configuration. Create either:\n"
                f"  1. qdrant.config.json at {qdrant_config_path} (recommended - simpler)\n"
                f"  2. .env.qdrant at {env_path}\n"
                f"  Or set MCP_ENV_FILE environment variable."
            )
    
    # 6. Load mcp-config.json
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 6. Replace env:VAR_NAME with actual values
    def resolve_env(value: Any) -> Any:
        if isinstance(value, str) and value.startswith("env:"):
            env_var = value[4:]
            env_value = os.getenv(env_var)
            if env_value is None:
                raise ValueError(f"{env_var} not found in .env.qdrant (loaded from {env_path})")
            return env_value
        elif isinstance(value, dict):
            return {k: resolve_env(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_env(item) for item in value]
        return value
    
    config_data = resolve_env(config_data)
    
    # 7. Validate and create Config object
    config = Config(**config_data)
    
    # 8. Set runtime paths
    config.project_root = project_root
    config.rag_server_dir = rag_server_dir
    
    return config

