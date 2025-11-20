"""
Tool Manifest System - Three-Tier Context Engineering

Implements context engineering optimization to prevent context rot:
- Tier 1: Lightweight tool briefs (30-50 tokens) - always loaded
- Tier 2: Strategy-specific schemas - loaded on selection
- Tier 3: Full execution - on-demand when tool is called

This prevents loading full tool schemas upfront, reducing context window usage.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class ToolBrief:
    """Lightweight tool description (Tier 1) - ~30-50 tokens"""
    name: str
    brief: str  # Short description, ~30-50 tokens
    category: str  # e.g., "search", "qa", "explanation"
    use_cases: List[str]  # 2-3 key use cases

@dataclass
class ToolSchema:
    """Full tool schema (Tier 2) - loaded on demand"""
    name: str
    description: str
    input_schema: dict
    examples: List[Dict[str, str]]  # Example queries/use cases

class ToolManifest:
    """
    Manages three-tier context engineering for MCP tools.
    
    Provides lightweight briefs for initial discovery, then full schemas
    on-demand when a tool is selected for use.
    """
    
    # Tier 1: Lightweight briefs (always loaded, ~30-50 tokens each)
    TOOL_BRIEFS: Dict[str, ToolBrief] = {
        "search": ToolBrief(
            name="search",
            brief="Semantic search across docs and code with filters. Returns relevant chunks with citations.",
            category="search",
            use_cases=[
                "Find specific information in documentation",
                "Search code by function or class name",
                "Filter results by content type or language"
            ]
        ),
        "ask": ToolBrief(
            name="ask",
            brief="Question-answering with full RAG pipeline. Uses intent classification, reranking, and synthesis.",
            category="qa",
            use_cases=[
                "Get answers to specific questions",
                "Compare different approaches or concepts",
                "Get clarifications on project details"
            ]
        ),
        "explain": ToolBrief(
            name="explain",
            brief="Comprehensive explanations with context and rationale. Groups results by document type.",
            category="explanation",
            use_cases=[
                "Understand flows, policies, or architecture",
                "Get detailed explanations with context",
                "Learn about system components"
            ]
        )
    }
    
    # Tier 2: Full schemas (loaded on-demand)
    # These are populated from actual tool definitions
    _tool_schemas: Dict[str, ToolSchema] = {}
    
    @classmethod
    def get_manifest(cls) -> Dict[str, dict]:
        """
        Get Tier 1 manifest - lightweight briefs for all tools.
        Returns minimal information (~30-50 tokens per tool).
        
        Returns:
            Dict mapping tool names to brief information
        """
        return {
            name: {
                "name": brief.name,
                "brief": brief.brief,
                "category": brief.category,
                "use_cases": brief.use_cases
            }
            for name, brief in cls.TOOL_BRIEFS.items()
        }
    
    @classmethod
    def get_tool_brief(cls, tool_name: str) -> Optional[dict]:
        """
        Get Tier 1 brief for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Brief information or None if not found
        """
        brief = cls.TOOL_BRIEFS.get(tool_name)
        if brief:
            return {
                "name": brief.name,
                "brief": brief.brief,
                "category": brief.category,
                "use_cases": brief.use_cases
            }
        return None
    
    @classmethod
    def register_tool_schema(cls, tool_name: str, description: str, 
                            input_schema: dict, examples: List[Dict[str, str]] = None):
        """
        Register Tier 2 schema for a tool (called when tool is selected).
        
        Args:
            tool_name: Name of the tool
            description: Full description
            input_schema: Complete input schema
            examples: Example use cases
        """
        cls._tool_schemas[tool_name] = ToolSchema(
            name=tool_name,
            description=description,
            input_schema=input_schema,
            examples=examples or []
        )
    
    @classmethod
    def get_tool_schema(cls, tool_name: str) -> Optional[dict]:
        """
        Get Tier 2 schema for a specific tool (loaded on-demand).
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Full schema or None if not found
        """
        schema = cls._tool_schemas.get(tool_name)
        if schema:
            return {
                "name": schema.name,
                "description": schema.description,
                "input_schema": schema.input_schema,
                "examples": schema.examples
            }
        return None
    
    @classmethod
    def get_all_schemas(cls) -> Dict[str, dict]:
        """
        Get all Tier 2 schemas (for compatibility mode).
        Use sparingly - prefer get_manifest() for initial discovery.
        
        Returns:
            Dict mapping tool names to full schemas
        """
        return {
            name: {
                "name": schema.name,
                "description": schema.description,
                "input_schema": schema.input_schema,
                "examples": schema.examples
            }
            for name, schema in cls._tool_schemas.items()
        }
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters).
        Used to ensure briefs stay within 30-50 token limit.
        """
        return len(text) // 4
    
    @classmethod
    def validate_briefs(cls) -> Dict[str, dict]:
        """
        Validate that all briefs are within token limits.
        
        Returns:
            Dict with validation results
        """
        results = {}
        for name, brief in cls.TOOL_BRIEFS.items():
            brief_text = f"{brief.brief} {' '.join(brief.use_cases)}"
            tokens = cls.estimate_tokens(brief_text)
            results[name] = {
                "tokens": tokens,
                "within_limit": 30 <= tokens <= 50,
                "brief": brief.brief
            }
        return results

