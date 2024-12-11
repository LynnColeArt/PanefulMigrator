# Paneful Migration Utility

## Overview
The Paneful Migration Utility is a tool designed to analyze, plan, and execute the reorganization of the Paneful art generation toolkit codebase. It provides comprehensive code analysis and guided migration to improve maintainability, implement proper design patterns, and ensure clear separation of concerns.

## Features

### Code Analysis
- **Class Structure Analysis**
  - Class relationships and dependencies
  - Inheritance hierarchies
  - Method and property tracking
  - Visual class diagrams (Mermaid)

- **Configuration Detection**
  - Hardcoded constants and magic numbers
  - Configuration-like patterns
  - Default parameters
  - Embedded resource paths
  - Suggestions for externalization

- **Complexity Analysis**
  - Cyclomatic complexity
  - Method and class metrics
  - Nesting depth
  - Coupling scores
  - Risk area identification

### Migration Planning
- Configurable migration mapping rules
- Detailed migration plan generation
- Dependency tracking
- Git history preservation
- Plan validation and conflict detection

### Project Organization
- Proper separation of concerns:
  - Core functionality
  - Transform operations
  - Resource management
  - User interfaces
- Design pattern implementation
- Resource organization

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd paneful2
```

2. Set up the migration utility:
```bash
cd migration_utility
python setup.py
```

## Usage

Run the utility:
```bash
python main.py
```

### Main Menu Options:
1. **Select Project to Analyze**
   - Choose a project or directory to analyze
   - View basic project statistics

2. **Project Overview**
   - File and directory statistics
   - Size distributions
   - Type breakdowns

3. **Class Structure Analysis**
   - View class relationships
   - Inheritance hierarchies
   - Method and property details
   - Visual class diagrams

4. **Configuration Analysis**
   - Identify embedded configuration
   - Group by location and type
   - Suggestions for externalization

5. **Complexity Analysis**
   - View complexity metrics
   - Identify risk areas
   - Get refactoring suggestions

6. **Migration Preview**
   - View planned changes
   - Check for conflicts
   - Review suggestions

7. **Run Migration**
   - Execute planned changes
   - Back up existing code
   - Preserve git history

## Project Structure

```
migration_utility/
├── core/
│   ├── analyzers/
│   │   ├── base.py
│   │   ├── class_analyzer.py
│   │   ├── config_analyzer.py
│   │   └── complexity_analyzer.py
│   ├── display.py
│   └── scanner.py
├── planner/
│   └── mapper.py
├── resources/
│   ├── directory_structure.yaml
│   └── migration_mapping.yaml
├── main.py
└── setup.py
```

## Configuration

### Migration Mapping
Configure migration rules in `resources/migration_mapping.yaml`:
- File type patterns
- Target locations
- Special handling rules
- Validation requirements

### Directory Structure
Define target structure in `resources/directory_structure.yaml`:
- Core components
- Transform operations
- Resource locations
- Interface organization

## Development

### Adding New Analyzers
1. Inherit from `BaseAnalyzer` in `core/analyzers/base.py`
2. Implement `analyze_file` method
3. Define analysis result dataclass
4. Update scanner integration

### Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### Testing
- Run tests: `python -m pytest tests/`
- Check code style: `flake8 .`

## Requirements
- Python 3.8+
- Required packages:
  ```
  pyyaml
  ```

## License
MIT License - See LICENSE file for details

## Support
- Issues: Submit via GitHub Issues
- Questions: See our [FAQ](docs/FAQ.md)
- Documentation: [Full Documentation](docs/index.md)

## Roadmap
- [ ] Enhanced pattern detection
- [ ] Interactive migration planning
- [ ] Integration with CI/CD
- [ ] Web interface for visualization
- [ ] Multi-project support

## Contributors
- Lynn Cole - Initial work

