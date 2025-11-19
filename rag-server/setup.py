#!/usr/bin/env python3
"""
Simple setup script for MCP RAG Server
Checks dependencies and creates necessary config files
"""
import json
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    # Map package names to import names
    required_packages = {
        'qdrant-client': 'qdrant_client',
        'sentence-transformers': 'sentence_transformers',
        'mcp': 'mcp',
        'pydantic': 'pydantic',
        'python-dotenv': 'dotenv',
        'markdown': 'markdown',
        'PyYAML': 'yaml',
        'tree-sitter': 'tree_sitter',
        'transformers': 'transformers'
    }
    
    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"[OK] {package_name}")
        except ImportError:
            print(f"[ERROR] {package_name} - not installed")
            missing.append(package_name)
    
    if missing:
        print(f"\n[WARNING] Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True

def create_qdrant_config():
    """Create qdrant.config.json if it doesn't exist"""
    base_dir = Path(__file__).parent
    config_path = base_dir / "qdrant.config.json"
    example_path = base_dir / "config" / "qdrant.config.example.json"
    if not example_path.exists():
        example_path = base_dir / "qdrant.config.example.json"
    
    if config_path.exists():
        print(f"[OK] qdrant.config.json already exists")
        return True
    
    if example_path.exists():
        # Copy example
        import shutil
        shutil.copy(example_path, config_path)
        print(f"[OK] Created qdrant.config.json from example")
        print(f"   [WARNING] Please edit {config_path} with your Qdrant credentials")
        return True
    else:
        # Create from scratch
        config = {
            "url": "https://your-cluster.qdrant.io:6333",
            "api_key": "your-api-key-here",
            "collection": "mcp-rag"
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Created qdrant.config.json")
        print(f"   [WARNING] Please edit {config_path} with your Qdrant credentials")
        return True

def check_project_config():
    """Check if mcp-config.json exists"""
    current_dir = Path(__file__).parent
    
    # Check in rag-server/ directory first
    config_path = current_dir / "mcp-config.json"
    if not config_path.exists():
        config_path = current_dir / "config" / "mcp-config.json"
    if not config_path.exists():
        config_path = current_dir / "config" / "mcp-config.example.json"
    
    if config_path.exists() and "example" not in str(config_path):
        print(f"[OK] Found mcp-config.json at {config_path}")
        return True
    else:
        print(f"[WARNING] mcp-config.json not found")
        print(f"   Create mcp-config.json in rag-server/ directory")
        if config_path.exists() and "example" in str(config_path):
            print(f"   Example available at: {config_path}")
        return False

def main():
    print("=" * 60)
    print("MCP RAG Server - Setup Verification")
    print("=" * 60)
    print()
    
    all_ok = True
    
    print("1. Checking Python version...")
    if not check_python_version():
        all_ok = False
    print()
    
    print("2. Checking dependencies...")
    if not check_dependencies():
        all_ok = False
    print()
    
    print("3. Setting up Qdrant configuration...")
    create_qdrant_config()
    print()
    
    print("4. Checking project configuration...")
    check_project_config()
    print()
    
    print("=" * 60)
    if all_ok:
        print("[OK] Setup complete! You're ready to start.")
        print()
        print("Next steps:")
        print("  1. Edit qdrant.config.json with your Qdrant credentials")
        print("  2. Create mcp-config.json in project root (if not exists)")
        print("  3. Run: python indexing/index_all.py --prune")
        print("  4. Run: python main.py")
    else:
        print("[WARNING] Setup incomplete. Please fix the issues above.")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

