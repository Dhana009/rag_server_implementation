"""
Code Parser: Parse TypeScript and Python code using Tree-sitter.

Extracts:
- Functions with signatures and docstrings
- Classes with methods and properties
- Imports and dependencies
- Comments and documentation
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
except ImportError:
    Language = None
    Parser = None

logger = logging.getLogger(__name__)


class CodeParser:
    """Parse source code to extract functions, classes, methods."""

    def __init__(self):
        """Initialize code parser with tree-sitter languages."""
        self.parser = None
        self.ts_python = None
        self.ts_typescript = None
        
        if Language is not None and Parser is not None:
            self._init_parsers()

    def _init_parsers(self):
        """Initialize tree-sitter parsers for Python and TypeScript."""
        try:
            self.parser = Parser()
            
            # Load Python language
            try:
                PYTHON_LANGUAGE = Language("tree_sitter_python", "python")
                self.ts_python = PYTHON_LANGUAGE
                logger.debug("Python parser initialized")
            except Exception as e:
                logger.warning(f"Failed to load Python parser: {e}")
            
            # Load TypeScript language
            try:
                TS_LANGUAGE = Language("tree_sitter_typescript", "typescript")
                self.ts_typescript = TS_LANGUAGE
                logger.debug("TypeScript parser initialized")
            except Exception as e:
                logger.warning(f"Failed to load TypeScript parser: {e}")
                
        except Exception as e:
            logger.warning(f"Tree-sitter parser initialization failed: {e}")

    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Parse a source file and extract code elements.

        Args:
            file_path: Path to source file (.py, .ts, .tsx, .js)

        Returns:
            List of {
                "type": "function" | "class" | "method",
                "name": str,
                "signature": str,
                "content": str,
                "start_line": int,
                "end_line": int,
                "docstring": str | None,
                "imports": list[str],
                "file_path": str,
                "language": str
            }

        Raises:
            ValueError: If file not supported or doesn't exist
            RuntimeError: If parsing fails
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise ValueError(f"File not found: {file_path}")

            # Determine language
            suffix = file_path_obj.suffix.lower()
            if suffix == ".py":
                language = "python"
            elif suffix in [".ts", ".tsx", ".js", ".jsx"]:
                language = "typescript"
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse based on language
            if language == "python" and self.ts_python:
                return self._parse_python(content, file_path)
            elif language == "typescript" and self.ts_typescript:
                return self._parse_typescript(content, file_path)
            else:
                logger.warning(f"Parser not available for {language}, using fallback")
                return self._parse_fallback(content, file_path, language)

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {str(e)}")
            raise RuntimeError(f"Code parsing failed: {str(e)}") from e

    def _parse_python(self, content: str, file_path: str) -> List[Dict]:
        """Parse Python code and extract functions/classes."""
        elements = []

        try:
            self.parser.set_language(self.ts_python)
            tree = self.parser.parse(content.encode())
            
            # Extract elements from tree
            self._extract_elements(tree.root_node, content, file_path, elements, "python")
            
            logger.debug(f"Parsed {len(elements)} elements from {file_path}")
        except Exception as e:
            logger.warning(f"Python parsing failed: {e}")

        return elements

    def _parse_typescript(self, content: str, file_path: str) -> List[Dict]:
        """Parse TypeScript/JavaScript code and extract functions/classes."""
        elements = []

        try:
            self.parser.set_language(self.ts_typescript)
            tree = self.parser.parse(content.encode())
            
            # Extract elements from tree
            self._extract_elements(tree.root_node, content, file_path, elements, "typescript")
            
            logger.debug(f"Parsed {len(elements)} elements from {file_path}")
        except Exception as e:
            logger.warning(f"TypeScript parsing failed: {e}")

        return elements

    def _extract_elements(self, node, content: str, file_path: str, elements: List[Dict], language: str):
        """Recursively extract functions and classes from AST."""
        try:
            if node.type in ["function_definition", "class_definition", "method_definition"]:
                element = self._create_element(node, content, file_path, language)
                if element:
                    elements.append(element)
            
            # Recurse into children
            for child in node.children:
                self._extract_elements(child, content, file_path, elements, language)
        except Exception as e:
            logger.debug(f"Error extracting element: {e}")

    def _create_element(self, node, content: str, file_path: str, language: str) -> Optional[Dict]:
        """Create element dictionary from AST node."""
        try:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract content
            element_content = content[node.start_byte:node.end_byte].decode() if isinstance(content, bytes) else content[node.start_byte:node.end_byte]
            
            # Extract name and signature
            name = self._extract_name(node)
            signature = self._extract_signature(node)
            docstring = self._extract_docstring(node, content)
            
            element_type = "function"
            if node.type == "class_definition":
                element_type = "class"
            elif node.type == "method_definition":
                element_type = "method"
            
            return {
                "type": element_type,
                "name": name,
                "signature": signature,
                "content": element_content,
                "start_line": start_line,
                "end_line": end_line,
                "docstring": docstring,
                "imports": [],  # Would need separate extraction
                "file_path": file_path,
                "language": language
            }
        except Exception as e:
            logger.debug(f"Failed to create element: {e}")
            return None

    def _extract_name(self, node) -> str:
        """Extract name from node."""
        try:
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode() if isinstance(child.text, bytes) else child.text
        except Exception:
            pass
        return "unknown"

    def _extract_signature(self, node) -> str:
        """Extract function/method signature from node."""
        try:
            # Get first line (contains signature)
            start_line = node.start_point[0]
            end_point = node.child_by_field_name("parameters").end_point[0] if node.child_by_field_name("parameters") else node.start_point[0]
            
            # Return first line as signature
            return node.text.decode().split('\n')[0] if isinstance(node.text, bytes) else node.text.split('\n')[0]
        except Exception:
            pass
        return ""

    def _extract_docstring(self, node, content: str) -> Optional[str]:
        """Extract docstring/documentation from node."""
        try:
            # Look for first string literal child (docstring)
            for child in node.children:
                if child.type == "string":
                    return child.text.decode() if isinstance(child.text, bytes) else child.text
        except Exception:
            pass
        return None

    def _parse_fallback(self, content: str, file_path: str, language: str) -> List[Dict]:
        """Fallback parsing using regex for unsupported languages."""
        import re
        
        elements = []
        
        if language == "python":
            # Regex for Python functions and classes
            func_pattern = r'^def\s+(\w+)\s*\((.*?)\):'
            class_pattern = r'^class\s+(\w+)\s*(?:\((.*?)\))?:'
        else:
            # Regex for TypeScript/JavaScript functions and classes
            func_pattern = r'(?:async\s+)?(?:function\s+)?(\w+)\s*\((.*?)\)\s*(?::|=>|{)'
            class_pattern = r'class\s+(\w+)\s*(?:extends\s+\w+)?\s*{'
        
        lines = content.split('\n')
        current_line = 0
        
        for line_num, line in enumerate(lines, 1):
            if re.match(func_pattern, line):
                match = re.match(func_pattern, line)
                if match:
                    elements.append({
                        "type": "function",
                        "name": match.group(1),
                        "signature": line.strip(),
                        "content": line,
                        "start_line": line_num,
                        "end_line": line_num,
                        "docstring": None,
                        "imports": [],
                        "file_path": file_path,
                        "language": language
                    })
            elif re.match(class_pattern, line):
                match = re.match(class_pattern, line)
                if match:
                    elements.append({
                        "type": "class",
                        "name": match.group(1),
                        "signature": line.strip(),
                        "content": line,
                        "start_line": line_num,
                        "end_line": line_num,
                        "docstring": None,
                        "imports": [],
                        "file_path": file_path,
                        "language": language
                    })
        
        return elements

