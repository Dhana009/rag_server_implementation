# Dockerfile for MCP RAG Server
# Located at repository root for Docker MCP Registry
# Builds the RAG server from rag-server/ subdirectory

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from rag-server subdirectory
COPY rag-server/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rag-server application code
COPY rag-server/ /app/

# Create necessary directories
RUN mkdir -p /app/qdrant_data /app/logs /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    TQDM_DISABLE=1 \
    MCP_SERVER_NAME=rag-server \
    PYTHONPATH=/app \
    MCP_PROJECT_ROOT=/workspace

# MCP servers communicate via stdio, so we expose no ports
# The server will be accessible through Docker Desktop's MCP Toolkit

# Default command - runs the MCP server
CMD ["python", "server.py"]

