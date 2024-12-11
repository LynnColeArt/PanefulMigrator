# core/analyzers/config_analyzer.py

import re
from .base import BaseAnalyzer, BaseAnalysis
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

@dataclass
class ConfigItem:
    """Information about a detected configuration item."""
    name: str
    value: Any
    location: str  # 'module', 'class', or 'function'
    context: str   # Full context (e.g., "class MyClass" or "function process_image")
    line_number: int
    suggestion: str

@dataclass
class ConfigAnalysis(BaseAnalysis):
    """Analysis results for configuration in a file."""
    config_items: List[ConfigItem]
    total_items: int
    by_location: Dict[str, List[ConfigItem]]  # Group by location type
    by_type: Dict[str, List[ConfigItem]]      # Group by value type

class ConfigAnalyzer(BaseAnalyzer):
    """Analyzes Python files for embedded configuration."""

    def __init__(self, logger=None):
        super().__init__(logger)
        
        # Configuration detection patterns
        self.patterns = {
            'names': {
                'prefix': {'CONFIG_', 'DEFAULT_', 'SETTINGS_', 'PARAM_'},
                'suffix': {'_CONFIG', '_SETTINGS', '_OPTIONS', '_DEFAULTS', '_PARAMS'},
                'whole': {'CONFIGURATION', 'SETTINGS', 'OPTIONS', 'PARAMETERS'}
            },
            'values': {
                'paths': r'^(?:/|[A-Za-z]:\\).*|.*\.(txt|json|yml|yaml|cfg|conf)$',
                'urls': r'^(http|https|ftp)://',
                'magic_numbers': {0, 1, 100, 1000, 60, 24, 365}
            }
        }
    
    def analyze_file(self, file_path: str) -> Optional[ConfigAnalysis]:
        """Analyze a Python file for configuration items."""
        tree = self.parse_file(file_path)
        if tree is None:
            return ConfigAnalysis(
                file_path=Path(file_path),
                success=False,
                error_message="Failed to parse file",
                config_items=[],
                total_items=0,
                by_location={},
                by_type={}
            )
        
        try:
            analysis = ConfigAnalysis(
                file_path=Path(file_path),
                success=True,
                config_items=[],
                total_items=0,
                by_location={},
                by_type={}
            )
            
            # Add parent links for context tracking
            self.add_parent_links(tree)
            
            # Walk the AST and collect configuration items
            self._analyze_node(tree, analysis)
            
            # Group items by location and type
            self._group_items(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return ConfigAnalysis(
                file_path=Path(file_path),
                success=False,
                error_message=str(e),
                config_items=[],
                total_items=0,
                by_location={},
                by_type={}
            )
    
    def _analyze_node(self, node: ast.AST, analysis: ConfigAnalysis, 
                     context: str = 'module'):
        """Recursively analyze AST nodes for configuration."""
        for node in ast.walk(node):
            if isinstance(node, ast.Assign):
                self._analyze_assignment(node, analysis, context)
                
            elif isinstance(node, ast.ClassDef):
                class_context = f"class {node.name}"
                for item in node.body:
                    self._analyze_node(item, analysis, class_context)
                
            elif isinstance(node, ast.FunctionDef):
                func_context = f"function {node.name}"
                self._analyze_function_defaults(node, analysis, func_context)
    
    def _analyze_assignment(self, node: ast.Assign, analysis: ConfigAnalysis, 
                          context: str):
        """Analyze an assignment node for configuration-like patterns."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                if self._is_config_name(name):
                    value = self.extract_value(node.value)
                    if value is not None:
                        item = ConfigItem(
                            name=name,
                            value=value,
                            location=context.split()[0],  # 'module', 'class', 'function'
                            context=context,
                            line_number=node.lineno,
                            suggestion=self._generate_suggestion(name, value)
                        )
                        analysis.config_items.append(item)
                        analysis.total_items += 1
    
    def _analyze_function_defaults(self, node: ast.FunctionDef, 
                                 analysis: ConfigAnalysis, context: str):
        """Analyze function default arguments for configuration-like values."""
        for arg, default in zip(node.args.args[-len(node.args.defaults):], 
                              node.args.defaults):
            value = self.extract_value(default)
            if value is not None and self._is_config_value(value):
                item = ConfigItem(
                    name=f"{node.name}_{arg.arg}_default",
                    value=value,
                    location='function',
                    context=context,
                    line_number=node.lineno,
                    suggestion=f"Consider making '{arg.arg}' configurable"
                )
                analysis.config_items.append(item)
                analysis.total_items += 1
    
    def _is_config_name(self, name: str) -> bool:
        """Check if a name matches configuration patterns."""
        upper_name = name.upper()
        
        # Check prefixes, suffixes, and whole words
        for prefix in self.patterns['names']['prefix']:
            if upper_name.startswith(prefix):
                return True
        
        for suffix in self.patterns['names']['suffix']:
            if upper_name.endswith(suffix):
                return True
        
        for whole in self.patterns['names']['whole']:
            if whole in upper_name:
                return True
        
        # Check if it's in CONSTANT_CASE
        return name.isupper() and '_' in name
    
    def _is_config_value(self, value: Any) -> bool:
        """Check if a value matches configuration patterns."""
        if isinstance(value, str):
            # Check paths and URLs
            for pattern in [self.patterns['values']['paths'], 
                          self.patterns['values']['urls']]:
                if re.match(pattern, value):
                    return True
        
        elif isinstance(value, (int, float)):
            return value in self.patterns['values']['magic_numbers']
        
        elif isinstance(value, (list, dict, tuple)):
            return True  # Collections often represent configuration
        
        return False
    
    def _generate_suggestion(self, name: str, value: Any) -> str:
        """Generate a suggestion for externalizing configuration."""
        if isinstance(value, str):
            if re.match(self.patterns['values']['paths'], value):
                return f"Move path '{name}' to configuration file"
            elif re.match(self.patterns['values']['urls'], value):
                return f"Move URL '{name}' to configuration file"
        
        elif isinstance(value, (list, dict)):
            return f"Move collection '{name}' to configuration file"
        
        elif isinstance(value, (int, float)):
            if value in self.patterns['values']['magic_numbers']:
                return f"Replace magic number '{value}' with configured value"
        
        return f"Consider making '{name}' configurable"
    
    def _group_items(self, analysis: ConfigAnalysis):
        """Group config items by location and type."""
        # Group by location
        for item in analysis.config_items:
            if item.location not in analysis.by_location:
                analysis.by_location[item.location] = []
            analysis.by_location[item.location].append(item)
        
        # Group by type
        for item in analysis.config_items:
            type_name = type(item.value).__name__
            if type_name not in analysis.by_type:
                analysis.by_type[type_name] = []
            analysis.by_type[type_name].append(item)
