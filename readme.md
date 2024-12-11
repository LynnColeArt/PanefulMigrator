# Paneful Migration Utility

## Overview
The Paneful Migration Utility analyzes and plans the reorganization of the Paneful art generation toolkit codebase. It provides code analysis tools to help identify areas needing refactoring and assists in planning code reorganization.

## Current Features

### Code Analysis
- **Class Structure Analysis**
  - Maps class relationships and dependencies
  - Tracks inheritance hierarchies
  - Generates Mermaid class diagrams

- **Configuration Detection**
  - Identifies hardcoded constants and magic numbers
  - Flags embedded configuration patterns
  - Suggests values for externalization

- **Complexity Analysis**
  - Measures cyclomatic complexity
  - Identifies complex methods and classes
  - Suggests potential refactoring points

## Project Structure
```
migration_utility/
├── core/
│   ├── analyzers/
│   │   ├── base.py           # Base analyzer functionality
│   │   ├── class_analyzer.py # Class structure analysis
│   │   ├── config_analyzer.py # Configuration detection
│   │   └── complexity_analyzer.py # Complexity metrics
│   ├── display.py           # User interface
│   └── scanner.py           # File scanning and analysis coordination
├── planner/
│   └── mapper.py            # Migration planning
├── resources/
│   ├── directory_structure.yaml  # Target structure definition
│   └── migration_mapping.yaml    # Migration rules
└── main.py                  # Main program entry
```

## Current Status
- Basic directory structure implemented
- Analysis components functional:
  - Class structure analysis
  - Configuration detection
  - Complexity metrics
- User interface for viewing results
- Migration execution not yet implemented

## Usage
```bash
python main.py
```

### Available Options:
1. Select Project to Analyze
2. Project Overview
3. View Class Structure Analysis
4. View Configuration Analysis
5. View Complexity Analysis
6. Preview Migration Plan
7. Run Migration (coming soon)
8. Exit

## Next Steps
- Implement migration execution
- Add validation tools
- Complete configuration menu
- Test with complex codebases

## Requirements
- Python 3.8+
- PyYAML

## Development
This is an active work in progress. Current focus is on implementing core analysis functionality and planning features.
