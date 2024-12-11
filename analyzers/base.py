# core/analyzers/base.py

import ast
from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from dataclasses import dataclass

@dataclass
class BaseAnalysis:
    """Base class for analysis results."""
    file_path: Path
    success: bool
    error_message: Optional[str] = None

class BaseAnalyzer(ABC):
    """Base class for all code analyzers."""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze_file(self, file_path: str) -> Optional[BaseAnalysis]:
        """Analyze a Python file. Must be implemented by subclasses."""
        pass
    
    def parse_file(self, file_path: str) -> Optional[ast.AST]:
        """Parse a Python file into an AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content)
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def safe_walk(self, node: ast.AST) -> ast.NodeVisitor:
        """Safely walk an AST node with error handling."""
        class SafeVisitor(ast.NodeVisitor):
            def __init__(self, logger):
                self.logger = logger
                self.errors = []
            
            def visit(self, node):
                try:
                    return super().visit(node)
                except Exception as e:
                    self.logger.warning(f"Error visiting node {type(node)}: {e}")
                    self.errors.append((node, str(e)))
        
        visitor = SafeVisitor(self.logger)
        visitor.visit(node)
        return visitor
    
    def extract_docstring(self, node: ast.AST) -> Optional[str]:
        """Safely extract docstring from an AST node."""
        try:
            return ast.get_docstring(node)
        except Exception:
            return None
    
    def get_line_range(self, node: ast.AST) -> tuple[int, int]:
        """Get the line range for a node."""
        try:
            return node.lineno, node.end_lineno
        except AttributeError:
            return 0, 0
    
    def count_lines(self, node: ast.AST) -> int:
        """Count the lines of code in a node."""
        start, end = self.get_line_range(node)
        return end - start + 1 if start and end else 0
    
    def get_node_source(self, node: ast.AST, file_content: str) -> Optional[str]:
        """Get the source code for a node."""
        try:
            lines = file_content.splitlines()
            start, end = self.get_line_range(node)
            if start and end and start <= len(lines):
                return '\n'.join(lines[start-1:end])
        except Exception as e:
            self.logger.warning(f"Error getting source for node: {e}")
        return None
    
    def extract_name(self, node: ast.AST) -> Optional[str]:
        """Safely extract name from a node."""
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self.extract_name(node.value)}.{node.attr}"
            elif isinstance(node, ast.FunctionDef):
                return node.name
            elif isinstance(node, ast.ClassDef):
                return node.name
        except Exception as e:
            self.logger.warning(f"Error extracting name from {type(node)}: {e}")
        return None
    
    def extract_value(self, node: ast.AST) -> Optional[Any]:
        """Safely extract a value from an AST node."""
        try:
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.List):
                return [self.extract_value(elt) for elt in node.elts]
            elif isinstance(node, ast.Dict):
                return {
                    self.extract_value(k): self.extract_value(v)
                    for k, v in zip(node.keys, node.values)
                }
            elif isinstance(node, ast.Name):
                if node.id in {'True', 'False', 'None'}:
                    return eval(node.id)
        except Exception as e:
            self.logger.warning(f"Error extracting value from {type(node)}: {e}")
        return None
    
    def find_parent_class(self, node: ast.AST) -> Optional[ast.ClassDef]:
        """Find the parent class of a node."""
        parent = getattr(node, 'parent', None)
        while parent:
            if isinstance(parent, ast.ClassDef):
                return parent
            parent = getattr(parent, 'parent', None)
        return None
    
    def analyze_imports(self, tree: ast.AST) -> Dict[str, str]:
        """Analyze import statements in an AST."""
        imports = {}
        try:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports[name.asname or name.name] = name.name
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        full_name = f"{module}.{name.name}"
                        imports[name.asname or name.name] = full_name
        except Exception as e:
            self.logger.warning(f"Error analyzing imports: {e}")
        return imports

    @staticmethod
    def add_parent_links(tree: ast.AST):
        """Add parent links to an AST."""
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                setattr(child, 'parent', parent)
