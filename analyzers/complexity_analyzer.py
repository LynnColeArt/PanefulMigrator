# core/analyzers/complexity_analyzer.py

from .base import BaseAnalyzer, BaseAnalysis
from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from pathlib import Path

@dataclass
class MethodComplexity:
    """Complexity metrics for a single method."""
    name: str
    cyclomatic_complexity: int
    line_count: int
    parameter_count: int
    local_var_count: int
    return_count: int
    nested_depth: int

@dataclass
class ClassComplexity:
    """Complexity metrics for a single class."""
    name: str
    method_count: int
    total_line_count: int
    instance_var_count: int
    methods: Dict[str, MethodComplexity]
    coupling_score: float
    inheritance_depth: int

@dataclass
class ComplexityAnalysis(BaseAnalysis):
    """Complete complexity analysis for a file."""
    total_complexity: float
    classes: Dict[str, ClassComplexity]
    global_scope_complexity: float
    highest_risk_areas: List[Dict[str, any]]
    suggestions: List[str]

class ComplexityAnalyzer(BaseAnalyzer):
    """Analyzes Python code complexity and identifies potential issues."""

    def __init__(self, logger=None):
        super().__init__(logger)
        
        # Thresholds for complexity warnings
        self.thresholds = {
            'method': {
                'cyclomatic': 10,      # Maximum cyclomatic complexity
                'lines': 50,           # Maximum lines per method
                'parameters': 5,       # Maximum parameters
                'nesting': 3           # Maximum nesting depth
            },
            'class': {
                'methods': 20,         # Maximum methods per class
                'lines': 300,          # Maximum lines per class
                'instance_vars': 10    # Maximum instance variables
            },
            'coupling': 5.0,          # Maximum coupling score
            'inheritance': 3           # Maximum inheritance depth
        }
    
    def analyze_file(self, file_path: str) -> Optional[ComplexityAnalysis]:
        """Analyze a Python file for complexity metrics."""
        tree = self.parse_file(file_path)
        if tree is None:
            return ComplexityAnalysis(
                file_path=Path(file_path),
                success=False,
                error_message="Failed to parse file",
                total_complexity=0.0,
                classes={},
                global_scope_complexity=0.0,
                highest_risk_areas=[],
                suggestions=[]
            )
        
        try:
            analysis = ComplexityAnalysis(
                file_path=Path(file_path),
                success=True,
                total_complexity=0.0,
                classes={},
                global_scope_complexity=0.0,
                highest_risk_areas=[],
                suggestions=[]
            )
            
            # Add parent links for better analysis
            self.add_parent_links(tree)
            
            # Analyze global scope
            analysis.global_scope_complexity = self._analyze_scope_complexity(tree)
            
            # Analyze classes
            self._analyze_classes(tree, analysis)
            
            # Calculate total complexity
            self._calculate_total_complexity(analysis)
            
            # Identify risk areas and generate suggestions
            self._identify_risks(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return ComplexityAnalysis(
                file_path=Path(file_path),
                success=False,
                error_message=str(e),
                total_complexity=0.0,
                classes={},
                global_scope_complexity=0.0,
                highest_risk_areas=[],
                suggestions=[]
            )
    
    def _analyze_scope_complexity(self, node: ast.AST) -> float:
        """Calculate complexity score for a scope."""
        complexity = 0.0
        
        for child in self.safe_walk(node).visit(node):
            # Control flow statements increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            
            # Complex expressions increase complexity
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_classes(self, tree: ast.AST, analysis: ComplexityAnalysis):
        """Analyze complexity of all classes in the file."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_analysis = self._analyze_class(node)
                analysis.classes[node.name] = class_analysis
    
    def _analyze_class(self, node: ast.ClassDef) -> ClassComplexity:
        """Analyze complexity metrics for a single class."""
        methods = {}
        instance_vars = set()
        
        # Analyze methods and collect instance variables
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods[item.name] = self._analyze_method(item)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    var_name = self.extract_name(target)
                    if var_name:
                        instance_vars.add(var_name)
        
        return ClassComplexity(
            name=node.name,
            method_count=len(methods),
            total_line_count=self.count_lines(node),
            instance_var_count=len(instance_vars),
            methods=methods,
            coupling_score=self._calculate_coupling_score(node),
            inheritance_depth=len(node.bases)
        )
    
    def _analyze_method(self, node: ast.FunctionDef) -> MethodComplexity:
        """Analyze complexity metrics for a single method."""
        local_vars = set()
        return_count = 0
        
        # Analyze method body
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                local_vars.add(child.id)
            elif isinstance(child, ast.Return):
                return_count += 1
        
        return MethodComplexity(
            name=node.name,
            cyclomatic_complexity=self._calculate_cyclomatic_complexity(node),
            line_count=self.count_lines(node),
            parameter_count=len(node.args.args),
            local_var_count=len(local_vars),
            return_count=return_count,
            nested_depth=self._calculate_nesting_depth(node)
        )
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a node."""
        def get_depth(node: ast.AST, current_depth: int) -> int:
            max_depth = current_depth
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(node, 0)
    
    def _calculate_coupling_score(self, node: ast.ClassDef) -> float:
        """Calculate coupling score based on dependencies."""
        # Use a set for unique external references
        external_refs = set()
        
        for child in ast.walk(node):
            name = self.extract_name(child)
            if name:
                external_refs.add(name)
        
        return len(external_refs) * 0.1
    
    def _calculate_total_complexity(self, analysis: ComplexityAnalysis):
        """Calculate total complexity score for the file."""
        total = analysis.global_scope_complexity
        
        for class_complexity in analysis.classes.values():
            # Add class-level complexity
            total += (
                class_complexity.method_count * 0.2 +
                class_complexity.coupling_score +
                class_complexity.inheritance_depth * 0.5
            )
            
            # Add method-level complexity
            for method in class_complexity.methods.values():
                total += (
                    method.cyclomatic_complexity * 0.3 +
                    (method.nested_depth ** 2) * 0.2 +
                    (method.parameter_count > self.thresholds['method']['parameters']) * 0.5
                )
        
        analysis.total_complexity = total
    
    def _identify_risks(self, analysis: ComplexityAnalysis):
        """Identify high-risk areas and generate refactoring suggestions."""
        for class_name, complexity in analysis.classes.items():
            # Check class-level metrics
            if complexity.method_count > self.thresholds['class']['methods']:
                self._add_risk(analysis, 'class', class_name, 
                             'Too many methods', 'Consider splitting into multiple classes')
            
            if complexity.total_line_count > self.thresholds['class']['lines']:
                self._add_risk(analysis, 'class', class_name,
                             'Excessive class size', 'Consider extracting functionality')
            
            # Check method-level metrics
            for method_name, method in complexity.methods.items():
                if method.cyclomatic_complexity > self.thresholds['method']['cyclomatic']:
                    self._add_risk(analysis, 'method', f'{class_name}.{method_name}',
                                 'High cyclomatic complexity', 'Simplify method logic')
                
                if method.nested_depth > self.thresholds['method']['nesting']:
                    self._add_risk(analysis, 'method', f'{class_name}.{method_name}',
                                 'Deep nesting', 'Refactor to reduce nesting')
    
    def _add_risk(self, analysis: ComplexityAnalysis, risk_type: str, 
                  location: str, issue: str, suggestion: str):
        """Add a risk area and corresponding suggestion."""
        analysis.highest_risk_areas.append({
            'type': risk_type,
            'location': location,
            'issue': issue
        })
        analysis.suggestions.append(f"{location}: {suggestion}")
