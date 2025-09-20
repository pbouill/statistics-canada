# CLI Tools

This directory contains command-line interface scripts that provide interactive and batch processing capabilities for the Statistics Canada package.

## Organization

**`tools/cli/` - Command-Line Interface Scripts:**
- **Interactive CLI tools** with user interfaces
- **Entry point scripts** with argparse command-line parsing
- **Batch processing scripts** for automated workflows

**`tools/` - Core Classes and Modules:**
- **Enum writer classes** (`wds_*_enum_gen.py`)
- **Core functionality** (`word_tracker.py`, `substitution.py`, etc.)
- **Data processing utilities** (`generate_enums.py`)
- **Supporting modules** (`abbreviations.py`, `enum_writer.py`)

## Available CLI Tools

### `main.py`
Main entry point for all tools operations. Provides a simple interface for common tasks.

```bash
python tools/cli/main.py
```

### `wds_enum_gen.py`
Command-line interface for generating WDS (Web Data Service) enumerations.

```bash
# Generate all WDS enums
python tools/cli/wds_enum_gen.py --type all --verbose

# Generate only ProductID enums
python tools/cli/wds_enum_gen.py --type product --verbose

# Generate only CodeSet enums
python tools/cli/wds_enum_gen.py --type codeset --verbose
```

### `interactive_abbreviation_manager.py`
Interactive tool for managing abbreviations used in enum generation.

```bash
python tools/cli/interactive_abbreviation_manager.py
```

### `unified_enum_processor.py`
Unified processor for all enum types with word tracking capabilities.

```bash
python tools/cli/unified_enum_processor.py --track-words
```

## VS Code Tasks

The following VS Code tasks are configured to run these CLI tools:

- **Generate WDS Enums (All)**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Generate WDS Enums (All)"
- **Generate ProductID Enums**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Generate ProductID Enums"  
- **Generate CodeSet Enums**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Generate CodeSet Enums"
- **Generate Geographic Enums**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Generate Geographic Enums"

## Design Principle

CLI scripts in this directory **use** the core classes and modules from the parent `tools/` directory but do not contain the core functionality themselves. This separation allows:

- **Reusability**: Core functionality can be imported by other parts of the system
- **Testability**: Core classes can be unit tested independently of CLI interfaces
- **Flexibility**: Multiple CLI interfaces can be built on the same core functionality
- **Maintainability**: Business logic is separated from user interface concerns
