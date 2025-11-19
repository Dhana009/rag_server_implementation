"""
Code Chunker: Create semantic chunks from parsed code.

Chunking strategy:
- Keep functions/methods as atomic chunks
- Include class context for methods
- Include imports for understanding
- Mark chunks with language and type metadata
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class CodeChunker:
    """Chunk parsed code elements into semantic chunks."""

    def chunk_code(self, parsed_elements: List[Dict], file_content: str) -> List[Dict]:
        """
        Create semantic chunks from parsed code elements.

        Args:
            parsed_elements: List of parsed code elements (from CodeParser)
            file_content: Original file content for context

        Returns:
            List of {
                "content": str,
                "start_line": int,
                "end_line": int,
                "metadata": {
                    "code_type": "function" | "class" | "method",
                    "name": str,
                    "language": str,
                    "imports": list[str],
                    "class_context": str | None,
                    "signature": str
                }
            }

        Raises:
            ValueError: If parsed_elements is empty
        """
        if not parsed_elements:
            raise ValueError("Cannot chunk empty parsed elements")

        chunks = []
        
        for element in parsed_elements:
            try:
                chunk = self._create_code_chunk(element, file_content)
                if chunk:
                    chunks.append(chunk)
            except Exception as e:
                logger.warning(f"Failed to chunk {element.get('name', 'unknown')}: {e}")

        logger.debug(f"Created {len(chunks)} code chunks from {len(parsed_elements)} elements")
        return chunks

    def _create_code_chunk(self, element: Dict, file_content: str) -> Dict:
        """
        Create a semantic chunk from a parsed element.

        Args:
            element: Parsed code element
            file_content: Original file content for extracting imports

        Returns:
            Chunk dictionary with content and metadata

        Raises:
            Exception: If chunk creation fails
        """
        # Extract imports from file
        imports = self._extract_imports(file_content, element.get("language", "python"))
        
        # Include imports in chunk content
        chunk_content = self._build_chunk_content(element, imports)
        
        return {
            "content": chunk_content,
            "start_line": element.get("start_line", 0),
            "end_line": element.get("end_line", 0),
            "metadata": {
                "code_type": element.get("type", "function"),
                "name": element.get("name", "unknown"),
                "language": element.get("language", "python"),
                "imports": imports,
                "class_context": None,  # Would be filled if method within class
                "signature": element.get("signature", ""),
            }
        }

    def _extract_imports(self, file_content: str, language: str) -> List[str]:
        """
        Extract import statements from file content.

        Args:
            file_content: Full file content
            language: Programming language

        Returns:
            List of import statements
        """
        imports = []
        lines = file_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if language == "python":
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
            else:  # TypeScript/JavaScript
                if line.startswith("import ") or line.startswith("require("):
                    imports.append(line)
        
        return imports[:10]  # Limit to first 10 imports

    def _build_chunk_content(self, element: Dict, imports: List[str]) -> str:
        """
        Build complete chunk content with context.

        Args:
            element: Parsed element
            imports: List of import statements

        Returns:
            Complete chunk content with imports and docstring
        """
        content_parts = []
        
        # Add relevant imports
        if imports:
            content_parts.append("# Imports:\n" + "\n".join(imports))
            content_parts.append("")
        
        # Add docstring if available
        if element.get("docstring"):
            content_parts.append(f"# Documentation:\n{element['docstring']}")
            content_parts.append("")
        
        # Add code
        content_parts.append(element.get("content", ""))
        
        return "\n".join(content_parts)

    def chunk_by_function_level(self, parsed_elements: List[Dict], file_content: str) -> List[Dict]:
        """
        Chunk code at function level (most granular).

        Strategy:
        - Each function/method is one chunk
        - Include class context if method
        - Include all imports at file level

        Args:
            parsed_elements: Parsed code elements
            file_content: Original file content

        Returns:
            Function-level chunks
        """
        return self.chunk_code(parsed_elements, file_content)

    def chunk_by_class_level(self, parsed_elements: List[Dict], file_content: str) -> List[Dict]:
        """
        Chunk code at class level (coarser granularity).

        Strategy:
        - Each class is one chunk (with all methods)
        - Top-level functions are individual chunks

        Args:
            parsed_elements: Parsed code elements
            file_content: Original file content

        Returns:
            Class-level chunks
        """
        chunks = []
        imports = self._extract_imports(file_content, parsed_elements[0].get("language", "python") if parsed_elements else "python")
        
        # Group methods by class
        classes = {}
        functions = []
        
        for element in parsed_elements:
            if element.get("type") == "class":
                classes[element["name"]] = element
            elif element.get("type") == "function":
                functions.append(element)
            # Methods are associated with their class separately
        
        # Create class chunks
        for class_name, class_element in classes.items():
            # Include all methods of this class
            class_methods = [e for e in parsed_elements if e.get("type") == "method" and e.get("class_context") == class_name]
            
            chunk_content = self._build_class_chunk(class_element, class_methods, imports)
            chunks.append({
                "content": chunk_content,
                "start_line": class_element.get("start_line", 0),
                "end_line": max([m.get("end_line", 0) for m in class_methods] + [class_element.get("end_line", 0)]),
                "metadata": {
                    "code_type": "class",
                    "name": class_name,
                    "language": class_element.get("language", "python"),
                    "imports": imports,
                    "class_context": None,
                    "signature": class_element.get("signature", ""),
                }
            })
        
        # Create function chunks
        for func_element in functions:
            chunk = self._create_code_chunk(func_element, file_content)
            chunks.append(chunk)
        
        return chunks

    def _build_class_chunk(self, class_element: Dict, methods: List[Dict], imports: List[str]) -> str:
        """Build chunk content for a class with all its methods."""
        content_parts = []
        
        # Add imports
        if imports:
            content_parts.append("# Imports:\n" + "\n".join(imports))
            content_parts.append("")
        
        # Add class
        content_parts.append(class_element.get("content", ""))
        
        # Add methods
        for method in methods:
            content_parts.append(f"\n# Method: {method.get('name', 'unknown')}\n")
            content_parts.append(method.get("content", ""))
        
        return "\n".join(content_parts)

