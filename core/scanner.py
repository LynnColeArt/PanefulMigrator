# core/scanner.py

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from .analyzers.class_analyzer import ClassAnalyzer, ClassAnalysis
from .analyzers.config_analyzer import ConfigAnalyzer, ConfigAnalysis
from .analyzers.complexity_analyzer import ComplexityAnalyzer, ComplexityAnalysis

@dataclass
class ProjectStats:
    """Statistics about project files and directories."""
    total_dirs: int
    total_files: int
    by_type: Dict[str, int]
    by_size: Dict[str, int]

@dataclass
class ProjectFile:
    """Information about a single project file."""
    path: Path
    size: int
    type: str

@dataclass
class ProjectAnalysis:
    """Complete analysis of a project file or directory."""
    path: Path
    stats: ProjectStats
    files: Dict[str, List[ProjectFile]]
    class_analysis: Optional[ClassAnalysis]
    config_analysis: Optional[ConfigAnalysis]
    complexity_analysis: Optional[ComplexityAnalysis]
    success: bool
    error_message: Optional[str] = None

class ProjectScanner:
    """Handles scanning and analysis of project files and directories."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.utility_dir = None
        self.logger = logging.getLogger('migration.scanner')
        
        # Initialize analyzers
        self.class_analyzer = ClassAnalyzer(self.logger)
        self.config_analyzer = ConfigAnalyzer(self.logger)
        self.complexity_analyzer = ComplexityAnalyzer(self.logger)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Initialize scanner-specific logging."""
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
    
    def set_utility_dir(self, utility_dir: str):
        """Set the migration utility directory to exclude from scanning."""
        self.utility_dir = Path(utility_dir)
        self.logger.info(f"Set utility directory: {utility_dir}")
    
    def _classify_file(self, path: Path) -> str:
        """Classify file by type based on extension and name."""
        name = path.name.lower()
        suffix = path.suffix.lower()
        
        if suffix == '.py':
            return 'python'
        elif suffix in ['.yml', '.yaml', '.json', '.cfg', '.conf']:
            return 'config'
        elif suffix in ['.md', '.txt', '.rst']:
            return 'docs'
        elif name.startswith('.git'):
            return 'git'
        elif suffix in ['.pyc', '.pyo'] or '__pycache__' in str(path):
            return 'compiled'
        else:
            return 'other'
    
    def scan_directory(self, dir_name: str) -> ProjectAnalysis:
        """Scan and analyze a project directory."""
        project_path = self.base_dir / dir_name
        self.logger.info(f"Scanning directory: {project_path}")
        
        try:
            # Initialize statistics
            stats = ProjectStats(
                total_dirs=0,
                total_files=0,
                by_type={},
                by_size={
                    'small': 0,    # < 10KB
                    'medium': 0,   # < 100KB
                    'large': 0     # >= 100KB
                }
            )
            
            files: Dict[str, List[ProjectFile]] = {
                'python': [],
                'config': [],
                'docs': [],
                'git': [],
                'compiled': [],
                'other': []
            }
            
            # Scan directory structure
            for item in project_path.rglob('*'):
                # Skip utility directory
                if self.utility_dir and self.utility_dir in item.parents:
                    continue
                
                if item.is_dir():
                    if not item.name == '__pycache__':
                        stats.total_dirs += 1
                elif item.is_file():
                    stats.total_files += 1
                    file_type = self._classify_file(item)
                    
                    # Update type statistics
                    stats.by_type[file_type] = stats.by_type.get(file_type, 0) + 1
                    
                    # Update size statistics
                    size = item.stat().st_size
                    if size < 10240:  # 10KB
                        stats.by_size['small'] += 1
                    elif size < 102400:  # 100KB
                        stats.by_size['medium'] += 1
                    else:
                        stats.by_size['large'] += 1
                    
                    # Store file information
                    files[file_type].append(ProjectFile(
                        path=item.relative_to(project_path),
                        size=size,
                        type=file_type
                    ))
            
            # Analyze Python files
            analyses = {
                'class': None,
                'config': None,
                'complexity': None
            }
            
            for file_info in files['python']:
                file_path = project_path / file_info.path
                
                # Run analyzers on Python files
                class_analysis = self.class_analyzer.analyze_file(str(file_path))
                if class_analysis and class_analysis.success:
                    analyses['class'] = class_analysis
                
                config_analysis = self.config_analyzer.analyze_file(str(file_path))
                if config_analysis and config_analysis.success:
                    analyses['config'] = config_analysis
                
                complexity_analysis = self.complexity_analyzer.analyze_file(str(file_path))
                if complexity_analysis and complexity_analysis.success:
                    analyses['complexity'] = complexity_analysis
            
            return ProjectAnalysis(
                path=project_path,
                stats=stats,
                files=files,
                class_analysis=analyses['class'],
                config_analysis=analyses['config'],
                complexity_analysis=analyses['complexity'],
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Error scanning directory {dir_name}: {e}")
            return ProjectAnalysis(
                path=project_path,
                stats=ProjectStats(0, 0, {}, {'small': 0, 'medium': 0, 'large': 0}),
                files={'python': [], 'config': [], 'docs': [], 'git': [], 
                      'compiled': [], 'other': []},
                class_analysis=None,
                config_analysis=None,
                complexity_analysis=None,
                success=False,
                error_message=str(e)
            )
    
    def list_available_projects(self) -> List[Dict[str, str]]:
        """List all available projects in the base directory."""
        projects = []
        
        try:
            for item in os.scandir(self.base_dir):
                # Skip utility directory
                if self.utility_dir and item.path == self.utility_dir:
                    continue
                
                if item.is_dir():
                    projects.append({
                        'name': item.name,
                        'type': 'directory',
                        'path': item.path
                    })
                elif item.name.endswith(('.py', '.md', '.txt', '.cfg', '.yml', '.yaml')):
                    projects.append({
                        'name': item.name,
                        'type': 'file',
                        'path': item.path
                    })
            
            return sorted(projects, key=lambda x: x['name'])
            
        except Exception as e:
            self.logger.error(f"Error listing projects: {e}")
            return []
    
    def get_project_summary(self, project_info: Dict[str, str]) -> Optional[Dict]:
        """Get a quick summary of a project without full analysis."""
        try:
            path = Path(project_info['path'])
            stat = path.stat()
            
            summary = {
                'name': project_info['name'],
                'type': project_info['type'],
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime
            }
            
            if project_info['type'] == 'directory':
                python_files = 0
                total_files = 0
                
                for item in path.rglob('*'):
                    if item.is_file():
                        total_files += 1
                        if item.suffix == '.py':
                            python_files += 1
                
                summary.update({
                    'total_files': total_files,
                    'python_files': python_files
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting summary for {project_info['name']}: {e}")
            return None
