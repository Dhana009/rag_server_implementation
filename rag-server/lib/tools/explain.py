from mcp.types import Tool
try:
    from ..core.vector_store import HybridVectorStore
    from ..utils.citation import format_citation
    from ..config import load_config
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.core.vector_store import HybridVectorStore
    from lib.utils.citation import format_citation
    from config import load_config

def explain_tool(topic: str) -> str:
    """
    Explain flows, policies, architecture, infrastructure
    
    Provides comprehensive explanations with context and rationale
    """
    try:
        config = load_config()
        store = HybridVectorStore(config)
        
        # Search for topic
        results = store.search(topic, top_k=config.max_results)
        
        if not results:
            return f"I couldn't find information about '{topic}'. Please try a different topic or use the search tool."
        
        # Build comprehensive explanation
        explanation = f"# Explanation: {topic}\n\n"
        
        # Group by doc type
        by_type = {}
        for result in results:
            doc_type = result.metadata.get('doc_type', 'other')
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result)
        
        # Organize by type
        type_order = ['flow', 'sdlc', 'policy', 'infrastructure', 'decision', 'other']
        for doc_type in type_order:
            if doc_type not in by_type:
                continue
            
            type_label = {
                'flow': 'Flows',
                'sdlc': 'SDLC Documentation',
                'policy': 'Policies & Standards',
                'infrastructure': 'Infrastructure',
                'decision': 'Decisions',
                'other': 'Other'
            }.get(doc_type, doc_type.title())
            
            explanation += f"## {type_label}\n\n"
            
            # Group by file
            file_groups = {}
            for result in by_type[doc_type]:
                if result.file_path not in file_groups:
                    file_groups[result.file_path] = []
                file_groups[result.file_path].append(result)
            
            for file_path, file_results in list(file_groups.items())[:2]:  # Top 2 files per type
                explanation += f"### {file_path}\n\n"
                for result in file_results[:2]:  # Top 2 chunks per file
                    citation = format_citation(result.file_path, result.line_number)
                    section = result.metadata.get('section', '')
                    if section:
                        explanation += f"**{section}** [{citation}]\n\n"
                    explanation += f"{result.content[:400].replace(chr(10), ' ')}\n\n"
        
        explanation += "\n---\n*For more details, use the search tool with specific queries.*"
        return explanation
    except Exception as e:
        return f"Error explaining topic: {str(e)}"

# MCP Tool definition
explain_tool_mcp = Tool(
    name="explain",
    description="Get comprehensive explanations of flows, policies, architecture, or infrastructure. Provides context and rationale.",
    inputSchema={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Topic to explain (e.g., 'phase-1 flows', 'selector policy', 'architecture rules', 'authentication flow')"
            }
        },
        "required": ["topic"]
    }
)
