# directory_mapper.py

import os
from pathlib import Path
from typing import List, Tuple

def should_exclude_dir(name: str) -> bool:
    """Check if directory should be completely skipped."""
    exclude_dirs = {
        '__pycache__', '.git', '.idea', '.vscode',
        'logs'
    }
    return name in exclude_dirs

def get_tree_elements(start_path: str) -> List[Tuple[int, str, bool]]:
    """Get list of (depth, name, is_dir) tuples for tree structure."""
    elements = []
    start_path = Path(start_path)

    for root, dirs, files in os.walk(start_path, topdown=True):
        # Skip excluded directories
        dirs[:] = sorted([d for d in dirs if not should_exclude_dir(d)])
        
        current_path = Path(root)
        depth = len(current_path.relative_to(start_path).parts)

        # Skip root directory itself
        if depth > 0:
            dir_name = current_path.name
            elements.append((depth - 1, dir_name, True))

        # Add files at current depth
        excluded_extensions = {'.pyc', '.pyo', '.pyd', '.log'}
        valid_files = sorted([f for f in files 
                            if not any(f.endswith(ext) for ext in excluded_extensions)])
        
        for filename in valid_files:
            elements.append((depth, filename, False))

    return elements

def create_directory_map(start_path: str) -> str:
    """Create a directory map with proper tree structure."""
    elements = get_tree_elements(start_path)
    output = []
    
    for i, (depth, name, is_dir) in enumerate(elements):
        prefix = '│   ' * depth
        
        # Determine if this is the last item at its level
        is_last = (i == len(elements) - 1 or 
                  elements[i + 1][0] <= depth)
        
        connector = '└──' if is_last else '├──'
        suffix = '/' if is_dir else ''
        
        output.append(f"{prefix}{connector} {name}{suffix}")

    return '\n'.join(output)

def main():
    current_dir = os.getcwd()
    print(f"\nMapping directory structure for: {current_dir}")
    print("=" * 50)
    
    directory_map = create_directory_map(current_dir)
    
    # Save to file
    output_file = 'migration_structure.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Migration Utility Structure - {current_dir}\n")
        f.write("=" * 50 + "\n")
        f.write(directory_map)
        
    # Display preview
    print(directory_map)
    print("\nStructure has been saved to:", output_file)

if __name__ == "__main__":
    main()
