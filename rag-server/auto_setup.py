#!/usr/bin/env python3
"""
Automated setup script for RAG Server
Run this to set up everything automatically without user intervention.

For AI Assistants: This script handles complete setup including:
- Python version verification
- Dependency installation
- Configuration file creation
- Cursor IDE integration
- Setup verification
"""
import sys
import json
import shutil
from pathlib import Path
import subprocess
import platform

def setup_rag_server():
    """Complete automated setup"""
    rag_server_dir = Path(__file__).parent.resolve()
    config_dir = rag_server_dir / "config"
    
    print("=" * 60)
    print("RAG Server - Automated Setup")
    print("=" * 60)
    print()
    
    # Step 1: Check Python
    print("[1/6] Verifying Python environment...")
    if sys.version_info < (3, 8):
        print(f"[ERROR] Python 3.8+ required, found {sys.version}")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"     Executable: {sys.executable}")
    print()
    
    # Step 2: Install dependencies
    print("[2/6] Installing dependencies...")
    requirements_file = rag_server_dir / "requirements.txt"
    if requirements_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                check=True, 
                capture_output=True,
                text=True
            )
            print("[OK] Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Dependency installation had issues:")
            print(f"         {e.stderr}")
            print("         You may need to run manually: pip install -r requirements.txt")
    else:
        print(f"[WARNING] requirements.txt not found at {requirements_file}")
    print()
    
    # Step 3: Create Qdrant config
    print("[3/6] Setting up Qdrant configuration...")
    qdrant_config = rag_server_dir / "qdrant.config.json"
    if not qdrant_config.exists():
        example = config_dir / "qdrant.config.example.json"
        if example.exists():
            shutil.copy(example, qdrant_config)
            print(f"[OK] Created {qdrant_config} from example")
        else:
            # Create minimal config with direct values (not env: references)
            with open(qdrant_config, 'w') as f:
                json.dump({
                    "url": "https://your-cluster.qdrant.io:6333",
                    "api_key": "your-api-key-here",
                    "collection": "mcp-rag"
                }, f, indent=2)
            print(f"[OK] Created {qdrant_config} with default values")
        print("     [ACTION REQUIRED] Edit this file with your Qdrant credentials")
        print("     Replace 'your-cluster.qdrant.io' and 'your-api-key-here' with actual values")
    else:
        print(f"[OK] {qdrant_config} already exists")
    print()
    
    # Step 4: Create project config
    print("[4/6] Setting up project configuration...")
    mcp_config = rag_server_dir / "mcp-config.json"
    
    # Auto-detect paths first (always do this to get actual project structure)
    project_root = rag_server_dir.parent
    docs = []
    code = []
    
    # Detect documentation
    if (project_root / "docs").exists():
        docs.append("docs/**/*.md")
    if (project_root / "README.md").exists():
        docs.append("README.md")
    # Always include rag-server docs for testing
    docs.append("rag-server/README.md")
    if (rag_server_dir / "custominstructions").exists():
        docs.append("rag-server/custominstructions/**/*.md")
    if not docs:
        docs = ["README.md"]
    
    # Detect code - check for common patterns
    code_found = False
    for pattern in ["src", "lib", "app", "backend", "frontend"]:
        if (project_root / pattern).exists():
            code.append(f"{pattern}/**/*.py")
            code_found = True
    
    # If no common folders, check if rag-server has code (for this project)
    if not code_found:
        # Count Python files in rag-server
        py_files = list(rag_server_dir.glob("**/*.py"))
        if py_files:
            code.append("rag-server/**/*.py")
            code_found = True
    
    # Fallback: search for any Python files
    if not code_found:
        all_py = list(project_root.glob("**/*.py"))
        if all_py:
            # Use a broad pattern but exclude common ignore dirs
            code.append("**/*.py")
        else:
            code = ["rag-server/**/*.py"]  # Default to rag-server at least
    
    if not mcp_config.exists():
        example = config_dir / "mcp-config.example.json"
        if example.exists():
            # Load example and update with detected paths
            with open(example, 'r') as f:
                config_data = json.load(f)
            # Override with auto-detected paths
            config_data["cloud_docs"] = docs
            config_data["code_paths"] = code[:5]  # Limit to 5
            with open(mcp_config, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"[OK] Created {mcp_config} from example with auto-detected paths")
        else:
            # Create config with auto-detected paths
            config_data = {
                "project_root": "..",
                "cloud_qdrant": {
                    "url": "https://your-cluster.qdrant.io:6333",
                    "api_key": "your-api-key-here",
                    "collection": "mcp-rag",
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "local_qdrant": {
                    "path": "./qdrant_data",
                    "collection": "mcp-rag-local",
                    "recreate_if_exists": False
                },
                "cloud_docs": docs,
                "local_docs": [],
                "decision_log_path": "docs/decisions/",
                "code_paths": code[:5],  # Limit to 5
                "embedding_models": {
                    "doc": "sentence-transformers/all-MiniLM-L6-v2",
                    "code": "microsoft/codebert-base",
                    "reranking": "cross-encoder/ms-marco-MiniLM-L-6-v2"
                },
                "hybrid_retrieval": {
                    "search_top_k": 20,
                    "rerank_top_k": 10,
                    "max_results": 25,
                    "hybrid_weights": {
                        "bm25": 0.3,
                        "vector": 0.7
                    }
                },
                "chunking": {
                    "doc_chunk_size": 1000,
                    "doc_chunk_overlap": 100,
                    "code_chunk_strategy": "function_level",
                    "code_chunk_overlap": 50
                }
            }
            
            with open(mcp_config, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"[OK] Created {mcp_config} with auto-detected paths")
        
        print(f"     Detected docs: {docs}")
        print(f"     Detected code: {code[:5]}")
        print(f"     [NOTE] Review and adjust paths in {mcp_config} if needed")
    else:
        print(f"[OK] {mcp_config} already exists")
        print(f"     Current paths:")
        try:
            with open(mcp_config, 'r') as f:
                existing_config = json.load(f)
            print(f"       Docs: {existing_config.get('cloud_docs', [])}")
            print(f"       Code: {existing_config.get('code_paths', [])}")
            print(f"     [TIP] If paths are wrong, update them manually or delete {mcp_config} and run setup again")
        except:
            pass
    print()
    
    # Step 5: Setup Cursor (optional)
    print("[5/6] Configuring Cursor IDE...")
    if platform.system() == "Windows":
        cursor_config = Path.home() / ".cursor" / "mcp.json"
    else:
        cursor_config = Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    
    if cursor_config.parent.exists():
        server_script = rag_server_dir / "server.py"
        python_exe = Path(sys.executable).resolve()
        
        # Detect server name from project root
        server_name = rag_server_dir.parent.name.lower().replace(" ", "-").replace("_", "-")
        if not server_name or server_name == ".":
            server_name = "rag-server"  # Generic fallback
        
        try:
            if cursor_config.exists():
                with open(cursor_config, 'r') as f:
                    mcp_data = json.load(f)
            else:
                mcp_data = {"mcpServers": {}}
            
            # Add or update server entry
            if "mcpServers" not in mcp_data:
                mcp_data["mcpServers"] = {}
            
            mcp_data["mcpServers"][server_name] = {
                "command": str(python_exe),
                "args": [str(server_script)]
            }
            
            with open(cursor_config, 'w') as f:
                json.dump(mcp_data, f, indent=2)
            print(f"[OK] Updated Cursor config at {cursor_config}")
            print(f"     Server name: {server_name}")
            print("     [ACTION REQUIRED] Restart Cursor IDE for changes to take effect")
        except Exception as e:
            print(f"[WARNING] Failed to update Cursor config: {e}")
    else:
        print("[SKIP] Cursor config directory not found (Cursor may not be installed)")
    print()
    
    # Step 6: Verify setup
    print("[6/6] Verifying setup...")
    setup_script = rag_server_dir / "setup.py"
    if setup_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(setup_script)], 
                capture_output=True, 
                text=True,
                cwd=str(rag_server_dir)
            )
            # Print output line by line for better formatting
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"     {line}")
            if result.returncode != 0 and result.stderr:
                print(f"[WARNING] Setup verification reported issues:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        print(f"     {line}")
        except Exception as e:
            print(f"[WARNING] Setup verification failed: {e}")
    else:
        print("[SKIP] setup.py not found")
    print()
    
    # Summary
    print("=" * 60)
    print("[OK] Automated setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Edit rag-server/qdrant.config.json with your Qdrant credentials")
    print("  2. Review rag-server/mcp-config.json and adjust paths if needed")
    print("  3. Run: cd rag-server && python rag_cli.py index")
    print("  4. Restart Cursor IDE if configured")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = setup_rag_server()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[ERROR] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

