# core/analyzers/class_analyzer.py

from .base import BaseAnalyzer, BaseAnalysis
from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from pathlib import Path

@dataclass
class ClassInfo:
    """Information about a single class definition."""
    name: str
    bases: List[str]
    methods: List[str]
    instance_vars: Set[str]
    dependencies: Set[str]
    line_count: int
    start_line: int
    end_line: int
    docstring: Optional[str]

@dataclass
class ClassAnalysis(BaseAnalysis):
    """Analysis results for all classes in a file."""
    classes: Dict[str, ClassInfo]
    relationships: Dict[str, Set[str]]  # Class -> dependent classes
    inheritance_tree: Dict[str, List[str]]  # Class -> subclasses

class ClassAnalyzer(BaseAnalyzer):
    """Analyzes Python files for class structures and relationships."""
    
    def analyze_file(self, file_path: str) -> Optional[ClassAnalysis]:
        """Analyze a Python file for class structures."""
        tree = self.parse_file(file_path)
        if tree is None:
            return ClassAnalysis(
                file_path=Path(file_path),
                success=False,
                error_message="Failed to parse file",
                classes={},
                relationships={},
                inheritance_tree={}
            )
        
        try:
            analysis = ClassAnalysis(
                file_path=Path(file_path),
                success=True,
                classes={},
                relationships={},
                inheritance_tree={}
            )
            
            # Add parent references for better analysis
            self.add_parent_links(tree)
            
            # Collect class information
            self._collect_classes(tree, analysis)
            
            # Analyze relationships
            self._analyze_relationships(analysis)
            self._build_inheritance_tree(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return ClassAnalysis(
                file_path=Path(file_path),
                success=False,
                error_message=str(e),
                classes={},
                relationships={},
                inheritance_tree={}
            )
    
    def _collect_classes(self, tree: ast.AST, analysis: ClassAnalysis):
        """Collect information about class definitions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self.extract_name(base) for base in node.bases]
                methods = []
                instance_vars = set()
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                instance_vars.add(target.id)
                
                analysis.classes[node.name] = ClassInfo(
                    name=node.name,
                    bases=bases,
                    methods=methods,
                    instance_vars=instance_vars,
                    dependencies=set(),
                    line_count=self.count_lines(node),
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    docstring=self.extract_docstring(node)
                )
    
    def _analyze_relationships(self, analysis: ClassAnalysis):
        """Analyze relationships between classes."""
        for class_name, class_info in analysis.classes.items():
            dependencies = set()
            
            # Check method signatures and body for dependencies
            for method in class_info.methods:
                for other_class in analysis.classes:
                    if other_class != class_name and other_class in method:
                        dependencies.add(other_class)
            
            # Add base classes as dependencies
            dependencies.update(class_info.bases)
            
            class_info.dependencies = dependencies
            analysis.relationships[class_name] = dependencies
    
    def _build_inheritance_tree(self, analysis: ClassAnalysis):
        """Build a hierarchy of class inheritance."""
        for class_name, class_info in analysis.classes.items():
            # Initialize inheritance tree entry
            if class_name not in analysis.inheritance_tree:
                analysis.inheritance_tree[class_name] = []
            
            # Add this class as a child of its bases
            for base in class_info.bases:
                if base not in analysis.inheritance_tree:
                    analysis.inheritance_tree[base] = []
                analysis.inheritance_tree[base].append(class_name)
    
    def generate_mermaid_diagram(self, analysis: ClassAnalysis) -> str:
        """Generate a Mermaid class diagram showing relationships."""
        if not analysis.success:
            return "classDiagram\n    note Error occurred during analysis"
            
        lines = ["classDiagram"]
        
        # Add inheritance relationships
        for base, children in analysis.inheritance_tree.items():
            for child in children:
                if child in analysis.classes:  # Only include classes we found
                    lines.append(f"    {base} <|-- {child}")
        
        # Add class details
        for class_name, info in analysis.classes.items():
            # Class box
            lines.append(f"    class {class_name} {{")
            
            # Add instance variables
            for var in sorted(info.instance_vars):
                lines.append(f"        +{var}")
            
            # Add methods
            for method in sorted(info.methods):
                lines.append(f"        +{method}()")
            
            lines.append("    }")
            
            # Add dependencies (excluding inheritance)
            for dep in info.dependencies - set(info.bases):
                if dep in analysis.classes:
                    lines.append(f"    {class_name} --> {dep}")
        
        return "\n".join(lines)
