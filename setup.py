# setup.py

import os
import logging
from datetime import datetime

def create_directory_structure():
    """Create the initial directory structure for the migration utility."""
    base_dirs = [
        'core',
        'planner',
        'resources',
        'logs'
    ]

    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create base directories
    for dir_name in base_dirs:
        dir_path = os.path.join(current_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        
        # Create __init__.py in Python module directories
        if dir_name in ['core', 'planner']:
            init_file = os.path.join(dir_path, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write(f"# {dir_name}/__init__.py\n")

    print("Created directory structure:")
    print(f"Root: {current_dir}")
    for dir_name in base_dirs:
        print(f"  ├── {dir_name}/")
        if dir_name in ['core', 'planner']:
            print(f"  │   └── __init__.py")

def main():
    try:
        create_directory_structure()
        print("\nDirectory structure created successfully.")
    except Exception as e:
        print(f"Error creating directory structure: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
