# planner/mapper.py

import os
import fnmatch
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
import yaml

class MigrationPlanner:
    """Handles planning and validation of file migrations."""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.logger = logging.getLogger('migration.planner')
        self.mapping_config = None
        self.current_plan = None
    
    def load_mapping(self, mapping_file: str) -> bool:
        """Load migration mapping configuration."""
        try:
            with open(mapping_file, 'r') as f:
                self.mapping_config = yaml.safe_load(f)
            
            # Validate mapping configuration
            if not self._validate_mapping_config():
                self.mapping_config = None
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading mapping file: {e}")
            return False
    
    def _validate_mapping_config(self) -> bool:
        """Validate the loaded mapping configuration."""
        required_keys = ['version', 'patterns', 'special', 'validation']
        
        for key in required_keys:
            if key not in self.mapping_config:
                self.logger.error(f"Missing required key in mapping: {key}")
                return False
        
        # Validate pattern structure
        patterns = self.mapping_config['patterns']
        if not isinstance(patterns, dict):
            self.logger.error("Patterns must be a dictionary")
            return False
            
        for file_type, pattern_list in patterns.items():
            if not isinstance(pattern_list, list):
                self.logger.error(f"Pattern list for {file_type} must be a list")
                return False
                
            for pattern in pattern_list:
                if not {'pattern', 'target', 'priority'}.issubset(pattern.keys()):
                    self.logger.error(f"Invalid pattern structure in {file_type}")
                    return False
        
        return True
    
    def create_migration_plan(self, project_contents: Dict) -> Dict:
        """Create a migration plan for the project contents."""
        if not self.mapping_config:
            raise ValueError("No mapping configuration loaded")
            
        self.current_plan = {
            'moves': [],      # (source, dest, pattern_used)
            'creates': [],    # directories to create
            'ignores': [],    # files/dirs being ignored
            'warnings': [],   # potential issues
            'errors': []      # blocking issues
        }
        
        try:
            # Plan directory structure
            self._plan_directory_structure()
            
            # Plan file migrations
            for file_type, files in project_contents['files'].items():
                if file_type in self.mapping_config['patterns']:
                    for file_info in files:
                        self._plan_file_migration(file_info, file_type)
                else:
                    self.current_plan['warnings'].append(
                        f"No mapping rules for file type: {file_type}")
            
            # Validate the plan
            self._validate_plan()
            
            return self.current_plan
            
        except Exception as e:
            self.logger.error(f"Error creating migration plan: {e}")
            self.current_plan['errors'].append(str(e))
            return self.current_plan
    
    def _plan_directory_structure(self):
        """Plan creation of required directory structure."""
        required_dirs = self.mapping_config['validation'].get('required_dirs', [])
        for dir_path in required_dirs:
            self.current_plan['creates'].append(dir_path)
        
        # Add directories needed by patterns
        for type_patterns in self.mapping_config['patterns'].values():
            for pattern in type_patterns:
                target = pattern['target']
                if '{' in target:
                    dir_path = target[:target.find('{')].rstrip('/')
                    if dir_path and dir_path not in self.current_plan['creates']:
                        self.current_plan['creates'].append(dir_path)
    
    def _plan_file_migration(self, file_info: Dict, file_type: str):
        """Plan migration for a single file."""
        file_path = file_info['path']
        
        # Check ignore patterns
        for ignore_pattern in self.mapping_config['special']['ignore']:
            if fnmatch.fnmatch(file_path, ignore_pattern):
                self.current_plan['ignores'].append(
                    (file_path, f"Matched ignore pattern: {ignore_pattern}"))
                return
        
        # Find matching pattern
        matched_pattern = None
        highest_priority = -1
        
        for pattern in self.mapping_config['patterns'][file_type]:
            if fnmatch.fnmatch(file_path, pattern['pattern']):
                priority = pattern['priority']
                if priority > highest_priority:
                    matched_pattern = pattern
                    highest_priority = priority
        
        if matched_pattern:
            try:
                target_path = self._resolve_target_path(file_path, matched_pattern['target'])
                self.current_plan['moves'].append((
                    file_path,
                    target_path,
                    matched_pattern['pattern']
                ))
            except Exception as e:
                self.current_plan['errors'].append(
                    f"Error planning move for {file_path}: {e}")
        else:
            self.current_plan['warnings'].append(
                f"No matching pattern for file: {file_path}")
    
    def _resolve_target_path(self, source_path: str, target_template: str) -> str:
        """Resolve target path pattern with actual values."""
        path = Path(source_path)
        
        replacements = {
            'name': path.name,
            'stem': path.stem,
            'parent': path.parent.name,
            'ext': path.suffix.lstrip('.')
        }
        
        result = target_template
        for key, value in replacements.items():
            placeholder = '{' + key + '}'
            if placeholder in result:
                result = result.replace(placeholder, value)
        
        if '{' in result or '}' in result:
            raise ValueError(f"Unresolved placeholders in target path: {result}")
        
        return result
    
    def _validate_plan(self):
        """Validate the complete migration plan."""
        # Check for duplicate targets
        seen_targets = {}
        for source, target, pattern in self.current_plan['moves']:
            if target in seen_targets:
                self.current_plan['errors'].append(
                    f"Duplicate target path {target} for files: "
                    f"{seen_targets[target]} and {source}")
            seen_targets[target] = source
        
        # Check for required directories
        required_dirs = set(self.mapping_config['validation']['required_dirs'])
        planned_dirs = set(self.current_plan['creates'])
        missing_dirs = required_dirs - planned_dirs
        if missing_dirs:
            self.current_plan['errors'].append(
                f"Missing required directories: {missing_dirs}")
        
        # Validate file sizes
        self._validate_file_sizes()
    
    def _validate_file_sizes(self):
        """Validate file sizes against configuration limits."""
        file_checks = self.mapping_config['validation'].get('file_checks', [])
        for check in file_checks:
            file_type = check['type']
            max_size = check.get('max_size')
            
            if max_size:
                for source, target, pattern in self.current_plan['moves']:
                    if Path(source).suffix.lstrip('.') == file_type:
                        size = os.path.getsize(
                            os.path.join(self.base_dir, source))
                        if size > max_size:
                            self.current_plan['warnings'].append(
                                f"File {source} exceeds maximum size for "
                                f"{file_type}: {size} > {max_size} bytes")
    
    def get_plan_summary(self) -> Dict:
        """Get a summary of the current migration plan."""
        if not self.current_plan:
            return None
            
        return {
            'total_moves': len(self.current_plan['moves']),
            'total_creates': len(self.current_plan['creates']),
            'total_ignores': len(self.current_plan['ignores']),
            'total_warnings': len(self.current_plan['warnings']),
            'total_errors': len(self.current_plan['errors']),
            'has_errors': len(self.current_plan['errors']) > 0
        }

