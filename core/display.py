# core/display.py

import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

class DisplayManager:
    """Handles all display and user interface functionality."""
    
    def __init__(self):
        self.current_project = None
    
    def show_main_menu(self) -> str:
        """Display main menu and get user selection."""
        self.clear_screen()
        print("\nPaneful Migration Utility")
        if self.current_project:
            print(f"Current Project: {self.current_project}")
        
        print("\nMain Menu:")
        print("1. Select Project to Analyze")
        print("2. Project Overview")
        
        if self.current_project:
            print("3. View Class Structure Analysis")
            print("4. View Configuration Analysis")
            print("5. View Complexity Analysis")
            print("6. Preview Migration Plan")
            print("7. Run Migration")
        else:
            print("3. View Class Structure Analysis [Select Project First]")
            print("4. View Configuration Analysis [Select Project First]")
            print("5. View Complexity Analysis [Select Project First]")
            print("6. Preview Migration Plan [Select Project First]")
            print("7. Run Migration [Select Project First]")
        
        print("8. Exit")
        return input("\nSelect an option: ").strip()
    
    def show_project_list(self, projects: List[Dict]) -> Optional[int]:
        """Display list of available projects and get selection."""
        self.clear_screen()
        print("\nAvailable Projects:")
        
        if not projects:
            print("No projects found.")
            input("\nPress Enter to continue...")
            return None
        
        for i, project in enumerate(projects, 1):
            project_type = project['type'].upper()
            name = project['name']
            print(f"{i}. [{project_type}] {name}")
        
        print("0. Back to Main Menu")
        
        choice = input("\nSelect project number: ").strip()
        if choice == "0":
            return None
            
        try:
            choice = int(choice)
            if 1 <= choice <= len(projects):
                return choice - 1
            else:
                print("Invalid selection.")
                input("\nPress Enter to continue...")
                return None
        except ValueError:
            print("Invalid input.")
            input("\nPress Enter to continue...")
            return None
    
    def show_project_analysis(self, analysis):
        """Display project overview and statistics."""
        self.clear_screen()
        print(f"\nProject Analysis: {self.current_project}")
        print("=" * 50)
        
        if not analysis.success:
            print(f"\nError during analysis: {analysis.error_message}")
            input("\nPress Enter to continue...")
            return
        
        # Basic Statistics
        print("\nProject Statistics:")
        print(f"Total Directories: {analysis.stats.total_dirs}")
        print(f"Total Files: {analysis.stats.total_files}")
        
        # Files by Type
        print("\nFiles by Type:")
        for file_type, count in analysis.stats.by_type.items():
            if count > 0:
                print(f"  {file_type}: {count}")
        
        # Size Distribution
        print("\nSize Distribution:")
        print(f"  Small (<10KB): {analysis.stats.by_size['small']}")
        print(f"  Medium (<100KB): {analysis.stats.by_size['medium']}")
        print(f"  Large (≥100KB): {analysis.stats.by_size['large']}")
        
        # Analysis Status
        print("\nAnalysis Status:")
        print(f"  Class Analysis: {'Available' if analysis.class_analysis else 'Not Available'}")
        print(f"  Config Analysis: {'Available' if analysis.config_analysis else 'Not Available'}")
        print(f"  Complexity Analysis: {'Available' if analysis.complexity_analysis else 'Not Available'}")
        
        input("\nPress Enter to continue...")
    
    def show_class_analysis(self, analysis):
        """Display class structure analysis results."""
        self.clear_screen()
        print("\nClass Structure Analysis")
        print("=" * 50)
        
        if not analysis.success:
            print(f"\nError during analysis: {analysis.error_message}")
            input("\nPress Enter to continue...")
            return
        
        # Class Overview
        print(f"\nFound {len(analysis.classes)} classes")
        
        # Class Relationships
        print("\nClass Relationships:")
        print("```mermaid")
        print(analysis.generate_mermaid_diagram())
        print("```")
        
        # Detailed Class Information
        print("\nDetailed Class Analysis:")
        for class_name, info in analysis.classes.items():
            print(f"\n{class_name}:")
            print(f"  Lines: {info.line_count} (lines {info.start_line}-{info.end_line})")
            if info.bases:
                print(f"  Inherits from: {', '.join(info.bases)}")
            print(f"  Methods ({len(info.methods)}):")
            for method in sorted(info.methods):
                print(f"    - {method}")
            if info.dependencies:
                print(f"  Dependencies: {', '.join(sorted(info.dependencies))}")
        
        input("\nPress Enter to continue...")
    
    def show_config_analysis(self, analysis):
        """Display configuration analysis results."""
        self.clear_screen()
        print("\nConfiguration Analysis")
        print("=" * 50)
        
        if not analysis.success:
            print(f"\nError during analysis: {analysis.error_message}")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nFound {analysis.total_items} configuration items")
        
        # Group by Location
        print("\nConfiguration by Location:")
        for location, items in analysis.by_location.items():
            print(f"\n{location.title()} Level ({len(items)}):")
            for item in items:
                print(f"  {item.name}:")
                print(f"    Value: {item.value}")
                print(f"    Line: {item.line_number}")
                print(f"    Suggestion: {item.suggestion}")
        
        # Group by Type
        print("\nConfiguration by Type:")
        for type_name, items in analysis.by_type.items():
            print(f"\n{type_name} ({len(items)}):")
            for item in items:
                print(f"  {item.name} = {item.value}")
        
        input("\nPress Enter to continue...")
    
    def show_complexity_analysis(self, analysis):
        """Display complexity analysis results."""
        self.clear_screen()
        print("\nComplexity Analysis")
        print("=" * 50)
        
        if not analysis.success:
            print(f"\nError during analysis: {analysis.error_message}")
            input("\nPress Enter to continue...")
            return
        
        # Overall Complexity
        print(f"\nTotal Complexity Score: {analysis.total_complexity:.2f}")
        print(f"Global Scope Complexity: {analysis.global_scope_complexity:.2f}")
        
        # Class Complexity
        print("\nClass Analysis:")
        for class_name, complexity in analysis.classes.items():
            print(f"\n{class_name}:")
            print(f"  Methods: {complexity.method_count}")
            print(f"  Lines: {complexity.total_line_count}")
            print(f"  Instance Variables: {complexity.instance_var_count}")
            print(f"  Coupling Score: {complexity.coupling_score:.2f}")
            print(f"  Inheritance Depth: {complexity.inheritance_depth}")
            
            print("\n  Method Complexity:")
            for method_name, method in complexity.methods.items():
                print(f"    {method_name}:")
                print(f"      Cyclomatic Complexity: {method.cyclomatic_complexity}")
                print(f"      Nested Depth: {method.nested_depth}")
                print(f"      Parameters: {method.parameter_count}")
        
        # Risk Areas
        if analysis.highest_risk_areas:
            print("\nHighest Risk Areas:")
            for risk in analysis.highest_risk_areas:
                print(f"\n  {risk['location']}:")
                print(f"    Issue: {risk['issue']}")
        
        # Suggestions
        if analysis.suggestions:
            print("\nRefactoring Suggestions:")
            for suggestion in analysis.suggestions:
                print(f"  - {suggestion}")
        
        input("\nPress Enter to continue...")
    
    def show_migration_plan(self, plan: Dict):
        """Display the migration plan details."""
        self.clear_screen()
        print("\nMigration Plan")
        print("=" * 50)
        
        if plan.get('errors'):
            print("\nErrors (must be resolved):")
            for error in plan['errors']:
                print(f"  ! {error}")
        
        if plan.get('warnings'):
            print("\nWarnings:")
            for warning in plan['warnings']:
                print(f"  * {warning}")
        
        print("\nDirectories to Create:")
        for dir_path in sorted(plan.get('creates', [])):
            print(f"  + {dir_path}")
        
        print("\nFiles to Move:")
        for source, target, pattern in sorted(plan.get('moves', [])):
            print(f"  {source}")
            print(f"    → {target}")
            print(f"    (using: {pattern})")
        
        if plan.get('ignores'):
            print("\nIgnored Items:")
            for path, reason in sorted(plan['ignores']):
                print(f"  - {path}")
                print(f"    ({reason})")
        
        self.confirm_action("Continue to main menu")
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_error(self, message: str):
        """Display error message."""
        print(f"\nError: {message}")
        input("\nPress Enter to continue...")
    
    def show_success(self, message: str):
        """Display success message."""
        print(f"\nSuccess: {message}")
        input("\nPress Enter to continue...")
    
    def confirm_action(self, action: str) -> bool:
        """Get user confirmation for an action."""
        response = input(f"\n{action} (y/N): ").strip().lower()
        return response == 'y'
