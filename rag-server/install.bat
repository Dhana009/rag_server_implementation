@echo off
REM Simple installation script for MCP RAG Server (Windows)

echo ==========================================
echo MCP RAG Server - Installation
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    exit /b 1
)
python --version
echo ✅ Python found
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    exit /b 1
)
echo ✅ Dependencies installed
echo.

REM Create config files if they don't exist
if not exist "qdrant.config.json" (
    if exist "qdrant.config.example.json" (
        copy qdrant.config.example.json qdrant.config.json >nul
        echo ✅ Created qdrant.config.json from example
        echo    ⚠️  Please edit qdrant.config.json with your Qdrant credentials
    )
)

echo.
echo ==========================================
echo ✅ Installation complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Edit qdrant.config.json with your Qdrant credentials
echo   2. Create mcp-config.json in your project root
echo   3. Run: python setup.py to verify setup
echo   4. Run: python indexing\index_all.py --prune to index content
echo   5. Run: python main.py to start the server
echo.

pause

