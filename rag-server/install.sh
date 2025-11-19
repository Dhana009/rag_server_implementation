#!/bin/bash
# Simple installation script for MCP RAG Server

echo "=========================================="
echo "MCP RAG Server - Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi
echo "✅ Python $python_version found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"
echo ""

# Create config files if they don't exist
if [ ! -f "qdrant.config.json" ]; then
    if [ -f "qdrant.config.example.json" ]; then
        cp qdrant.config.example.json qdrant.config.json
        echo "✅ Created qdrant.config.json from example"
        echo "   ⚠️  Please edit qdrant.config.json with your Qdrant credentials"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit qdrant.config.json with your Qdrant credentials"
echo "  2. Create mcp-config.json in your project root"
echo "  3. Run: python setup.py to verify setup"
echo "  4. Run: python indexing/index_all.py --prune to index content"
echo "  5. Run: python main.py to start the server"
echo ""

