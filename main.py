# main.py

import os
import logging
from pathlib import Path
from datetime import datetime
from core.scanner import ProjectScanner
from core.display import DisplayManager
from planner.mapper import MigrationPlanner

class MigrationUtility:
    """Main migration utility coordinator."""
    
    def __init__(self):
        print("Initializing Migration Utility...")
        self.base_dir = self._find_base_dir()
        self.utility_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up component managers
        self.display = DisplayManager()
        self.scanner = ProjectScanner(self.base_dir)
        self.scanner.set_utility_dir(str(self.utility_dir))
        self.planner = MigrationPlanner(self.base_dir)
        
        # Initialize state
        self.current_analysis = None
        
        # Ensure required directories exist
        self.resources_dir = self.utility_dir / "resources"
        self.migrated_dir = self.utility_dir / "migrated"
        os.makedirs(self.resources_dir, exist_ok=True)
        os.makedirs(self.migrated_dir, exist_ok=True)
        
        self._setup_logging()
        logging.info("Migration utility initialized")
    
    def _find_base_dir(self) -> str:
        """Find the base directory (one level up from utility)."""
        return str(Path(__file__).parent.parent)
    
    def _setup_logging(self):
        """Initialize logging configuration."""
        log_dir = self.utility_dir / "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = log_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def handle_project_selection(self) -> bool:
        """Handle project selection process."""
        projects = self.scanner.list_available_projects()
        selection = self.display.show_project_list(projects)
        
        if selection is not None:
            project = projects[selection]
            self.display.current_project = project['name']
            
            # Perform full analysis
            self.current_analysis = self.scanner.scan_directory(project['name'])
            
            if not self.current_analysis.success:
                self.display.show_error(
                    f"Analysis failed: {self.current_analysis.error_message}")
                return False
            
            return True
            
        return False
    
    def handle_project_analysis(self):
        """Display current project analysis results."""
        if not self.current_analysis:
            self.display.show_error("No project analysis available")
            return
        
        self.display.show_project_analysis(self.current_analysis)
    
    def handle_structural_analysis(self):
        """Display class structure analysis results."""
        if not self.current_analysis or not self.current_analysis.class_analysis:
            self.display.show_error("No class analysis available")
            return
            
        self.display.show_class_analysis(self.current_analysis.class_analysis)
    
    def handle_config_analysis(self):
        """Display configuration analysis results."""
        if not self.current_analysis or not self.current_analysis.config_analysis:
            self.display.show_error("No configuration analysis available")
            return
            
        self.display.show_config_analysis(self.current_analysis.config_analysis)
    
    def handle_complexity_analysis(self):
        """Display complexity analysis results."""
        if not self.current_analysis or not self.current_analysis.complexity_analysis:
            self.display.show_error("No complexity analysis available")
            return
            
        self.display.show_complexity_analysis(self.current_analysis.complexity_analysis)
    
    def handle_migration_preview(self):
        """Handle migration plan preview."""
        if not self.current_analysis:
            self.display.show_error("No project analysis available")
            return
        
        mapping_file = self.resources_dir / 'migration_mapping.yaml'
        if not mapping_file.exists():
            self.display.show_error("Migration mapping not found")
            return
        
        if self.planner.load_mapping(str(mapping_file)):
            plan = self.planner.create_migration_plan(self.current_analysis)
            self.display.show_migration_plan(plan)
        else:
            self.display.show_error("Failed to load migration mapping")
    
    def handle_migration_execution(self):
        """Handle actual migration execution."""
        if not self.current_analysis:
            self.display.show_error("No project analysis available")
            return
            
        if not self.display.confirm_action(
            "Are you sure you want to perform the migration?"):
            return
            
        # Create backup first
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{self.display.current_project}_{timestamp}"
        
        try:
            # TODO: Implement actual migration execution
            self.display.show_error("Migration execution coming soon")
        except Exception as e:
            self.display.show_error(f"Migration failed: {e}")
    
    def run(self):
        """Main program loop."""
        while True:
            choice = self.display.show_main_menu()
            
            try:
                if choice == "1":
                    self.handle_project_selection()
                    
                elif choice == "2":
                    self.handle_project_analysis()
                    
                elif choice == "3":
                    self.handle_structural_analysis()
                    
                elif choice == "4":
                    self.handle_config_analysis()
                    
                elif choice == "5":
                    self.handle_complexity_analysis()
                    
                elif choice == "6":
                    self.handle_migration_preview()
                    
                elif choice == "7":
                    self.handle_migration_execution()
                    
                elif choice == "8":
                    print("\nExiting Migration Utility...")
                    break
                    
                else:
                    self.display.show_error("Invalid option selected")
                    
            except Exception as e:
                logging.error(f"Error in main loop: {e}", exc_info=True)
                self.display.show_error(f"An error occurred: {str(e)}")

def main():
    try:
        utility = MigrationUtility()
        utility.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error("Fatal error", exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
