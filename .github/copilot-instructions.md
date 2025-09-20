# Statistics Canada Python Bindings - AI Coding Instructions

## Architecture Overview

This is a Python package providing bindings for Statistics Canada's Web Data Service (WDS) API and census data processing. The architecture follows a layered approach:

### Core Components
- **`statscan/wds/`**: Main WDS API client with async HTTP operations (`client.py` contains the `WDS` class)
- **`statscan/enums/`**: Hierarchical geographic enumerations with auto-generated code from census data
- **`statscan/sdmx/`**: SDMX (Statistical Data and Metadata eXchange) data models using Pydantic
- **`statscan/util/`**: Data download/processing utilities with async operations
- **`tools/generate_enums.py`**: Code generation system for geographic enumerations
- **`tools/wds_productid_enum_gen.py`**: Optimized ProductID enum generator for WDS cubes
- **`tools/wds_code_enum_gen.py`**: Optimized CodeSet enum generator for WDS code sets

### Directory Layout ###
- **`debug/`**: Debugging tools and scripts
- **`docs/`**: Documentation files
- **`examples/`**: Example scripts and notebooks
- **`statscan/`**: Main package directory
  - **`wds/`**: WDS API client
  - **`enums/`**: Geographic enumerations
  - **`sdmx/`**: SDMX data models
  - **`util/`**: Utility functions
- **`tests/`**: Test suite
  - **`data/`**: Test data files
  - **`unit/`**: Unit tests
  - **`integration/`**: Integration tests
- **`tools/`**: Code generation scripts
- **`scratch/`**: Scratchpad for experimentation, debug files, and temporary outputs


## Primary Focus: WDS API vs SDMX Processing

**🎯 PRIMARY OBJECTIVE: WDS (Web Data Service) API**
- **WDS is the main focus** - simpler, more direct API calls to Statistics Canada
- **📚 OFFICIAL REFERENCE**: https://www.statcan.gc.ca/en/developers/wds/user-guide - **USE THIS GUIDE FOR ALL WDS DEVELOPMENT**
- **Direct JSON responses** - easier to parse and work with than SDMX XML
- **Real-time data access** - live API calls for current statistics
- **Clean async interface** - `statscan.wds.client.Client` provides 30+ endpoints
- **Current development priority** - all new features should focus on WDS

**📊 SECONDARY: SDMX (Statistical Data and Metadata eXchange) Processing**
- **Legacy/compatibility layer** - complex XML-based international standard
- **Batch/bulk data processing** - larger datasets but more complex parsing
- **Future enhancement** - can be revisited later once WDS functionality is complete
- **Limited current use** - maintain existing code but don't prioritize new SDMX features

**Key Principle**: When building new features, **always prefer WDS API over SDMX** unless specifically required for compatibility.

### Data Flow Architecture
1. **🏆 WDS API Layer**: `Client` class in `wds/client.py` provides async methods for 30+ Statistics Canada endpoints
2. **📊 SDMX Model Layer**: Pydantic models in `sdmx/` handle legacy SDMX response serialization (secondary priority)
3. **🗺️ Enum Layer**: Auto-generated geographic enums in `enums/auto/` with parent classes in `enums/geocode/`
4. **🔧 Utility Layer**: `util/get_data.py` handles file downloads and DataFrame operations

## Development Workflows

### Environment Setup
```bash
# Python 3.11+ required - check pyproject.toml for version constraints
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.dev.txt  # Installs package in editable mode via -e .
```

### Virtual Environment Activation
**CRITICAL**: Always activate the virtual environment before running any Python scripts:
```bash
source .venv/bin/activate  # Linux/Mac
# OR for Windows:
# .venv\Scripts\activate
```
This ensures proper dependency isolation and prevents version conflicts.

### Testing Strategy
- **Primary Framework**: All tests MUST use pytest and be placed in the `tests/` directory
- **Test Execution**: Use `python -m pytest tests/ -v` for running tests
- **Test Compatibility**: All test files must be pytest-compatible (use `test_*.py` naming convention)
- **Test Organization**: 
  - `tests/unit/`: Unit tests for individual components
  - `tests/integration/`: Integration tests requiring external API calls
  - `tests/data/`: Test data files and fixtures
  - `tests/`: Root level for cross-cutting tests and utilities
- **Async Testing**: Uses `pytest-asyncio` for async test methods with `@pytest.mark.asyncio` decorator
- **Fixtures**: Use pytest fixtures for setup/teardown and shared test data
- **Integration Tests**: Require internet access for WDS API calls - mark with `@pytest.mark.integration`
- **Legacy Compatibility**: `python tests/run_tests.py` provides unittest fallback but new tests should be pure pytest

### Code Generation Workflow
**Critical**: Geographic enumerations are auto-generated from Statistics Canada data:
```bash
python tools/generate_enums.py  # Downloads census data and regenerates enums/auto/ files
```
- Never manually edit files in `statscan/enums/auto/` - they are overwritten
- Modify templates in `tools/generate_enums.py` and parent classes in `enums/geocode/`
- Uses pandas to process census CSV data and generates Enum classes with proper inheritance

### Abbreviation System for Enum Generation
**Critical**: WDS enum identifiers are compressed using a sophisticated substitution system:
- **`tools/abbreviations.py`**: Contains `DEFAULT_ABBREVIATIONS` dictionary with root word mappings
- **`tools/substitution.py`**: `SubstitutionEngine` extends abbreviations via morphological variants using NLTK and pyinflect
- **`tools/word_tracker.py`**: Word tracking system for identifying new abbreviation opportunities during enum generation
- **`tools/find_abbreviation_opportunities.py`**: Comprehensive analysis tool for discovering and prioritizing potential abbreviations
- **`tools/review_abbreviations.py`**: Quality assurance tool for validating abbreviation dictionary integrity
- **`tools/interactive_abbreviation_manager.py`**: Enhanced interactive system for adding new abbreviations and applying consolidation opportunities
- **`tools/unified_enum_processor.py`**: Single entry point for processing all enum types with consistent word tracking
- **Morphological Extension**: Root words like "empl" automatically cover "employ", "employment", "employed", "employees", etc.
- **Testing Coverage**: Use `SubstitutionEngine._generate_variants_static("word")` to test morphological coverage before adding new abbreviations
- **Performance Impact**: Proper abbreviations reduce enum identifier length from 150+ chars to manageable names
- **Word Tracking Workflow**: 
  1. Run `python tools/unified_enum_processor.py --track-words` to collect word frequency data across all generators
  2. Use `python tools/find_abbreviation_opportunities.py` for comprehensive analysis with smart suggestions
  3. Run `python tools/interactive_abbreviation_manager.py` for user-friendly abbreviation selection and implementation
  4. Validate changes with morphological testing and conflict detection before committing
- **Interactive Enhancement**: Discovered abbreviation opportunities are automatically integrated into user workflow with smart suggestions, conflict detection, and quality validation

### Build Process
- **Version**: Auto-generated in `_version.py` with format `YYYY.M.D.HHMMSS`
- **Package**: Uses `python -m build --no-isolation` (not setuptools directly)
- **CI**: GitHub Actions test on Python 3.11-3.13, build artifacts stored

## Project-Specific Patterns

### Async API Pattern
All WDS operations are async - use this pattern:
```python
from statscan.wds.client import WDS

async def get_data():
    client = WDS()
    return await client.get_cube_metadata(product_id=123)

# In tests/scripts: asyncio.run(get_data())
```

### Geographic Enum Hierarchy
Geographic enums inherit capabilities based on containment:
- `ProvinceTerritory` → `ProvinceGeoCode` → `GeoCode`
- `CensusDivision` → `CensusDivisionGeoCode` → `ProvinceGeoCode`
- Each level adds specific `get_schema()` and geographic validation methods

### Model Validation Pattern
SDMX models use Pydantic with preprocessing hooks:
```python
class CustomModel(Base):
    @classmethod
    def _preprocess_data(cls, data: dict) -> dict:
        # Clean/transform data before validation
        return data
```

### Error Handling Convention
- **WDS Client**: Uses `response.raise_for_status()` and checks `status` field in JSON
- **Data Processing**: Pandas operations with `.dropna()` for geographic data cleanup
- **Enum Generation**: Validates required columns exist before processing

## Integration Points

### External Dependencies
- **HTTPX**: Async HTTP client for WDS API calls - prefer over requests
- **Pandas**: Census data processing - required for enum generation
- **Pydantic**: Response models with validation - all SDMX models inherit from `Base`

### Statistics Canada APIs

**🚨 CRITICAL WDS API REFERENCE 🚨**
- **📚 WDS User Guide**: **https://www.statcan.gc.ca/en/developers/wds/user-guide**
  - **🎯 MANDATORY REFERENCE**: **ALL WDS API development MUST follow this official guide**
  - **📖 Primary Documentation**: Use this guide for API functionality validation, endpoint specifications, and parameter requirements
  - **🔄 Always Validate Against Guide**: When implementing new WDS features, cross-reference with official documentation
  - **🚀 Troubleshooting First**: Check the User Guide before diagnosing API issues

**WDS API Core Details:**
- **Base URL**: Configured in `statscan/url.py` as `WDS_URL` 
- **Authentication**: No authentication required for public WDS endpoints
- **Rate Limits**: 50 requests/second server-wide, 25 requests/second per IP address
- **Service Hours**: 24/7 operation with data updates at 8:30 AM EST on business days
- **Response Format**: All responses follow `{"status": "SUCCESS/FAILED", "object": {...}}` structure
- **Key Methods**: getCubeMetadata, getSeriesInfoFromCubePidCoord, getDataFromCubePidCoordAndLatestNPeriods
- **Coordinate Format**: Dot-separated member IDs (e.g., "1.3.1.1.1.1.0.0.0.0") with max 10 dimensions
- **Product ID Format**: 8-10 digit identifier where first 2 digits = subject, digits 3-4 = product type, remainder = sequential
- **Census Products**: Use 9810xxxx product ID range for census data (e.g., 98100002 for population/dwellings)

**Other Data Sources:**
- **Geographic Data**: Downloads from `GEO_ATTR_FILE_2021_URL` for enum generation

### MCP Server
- **`statscan/mcp_server.py`**: Model Context Protocol server for AI integration
- **Resources**: Exposes WDS requests, version info, and code sets via MCP
- **Usage**: Run with `python -m statscan.mcp_server` for AI tool integration

## Critical Development Notes

- **Never commit** auto-generated files in `statscan/enums/auto/` to git
- **Always use absolute imports** within the package (e.g., `from statscan.enums.schema import Schema`)
- **Async contexts required** for WDS client operations - don't use sync patterns
- **Geographic codes follow DGUID format**: `{Year:4}{Schema:5}{Province:2}{Identifier:N}`

### 🚨 **CRITICAL FILE ORGANIZATION RULES** 🚨

**NEVER CREATE FILES IN ROOT DIRECTORY** - All files must be placed in appropriate subdirectories:

- **`tests/`**: ALL test files must be in `tests/` directory (never in root), must use pytest conventions
- **`examples/`**: Demo scripts and educational examples go in `examples/` directory  
- **`scratch/`**: **ALL debug files, temporary outputs, generated reports, and experimental scripts MUST be in `scratch/` directory**
- **`tools/`**: Production code generation and utility scripts only in `tools/` directory
- **`docs/`**: Official package documentation only

**🔥 IMMEDIATE ACTION REQUIRED**: When creating ANY debug script, investigation file, or temporary analysis:
- Create it in `scratch/` directory: `scratch/debug_*.py`, `scratch/investigate_*.py`, etc.
- NEVER create `debug_*.py`, `test_*.py` or similar files in root directory
- Use `create_file` with path like `/home/pbouill/VS Code Projects/statistics-canada/scratch/debug_analysis.py`

**🚨 COMMON VIOLATIONS TO AVOID**:
- ❌ **Demo files in `tools/`**: Move `demo_*.py` files to `examples/`
- ❌ **Python scripts in `tests/data/`**: Only JSON/CSV data files allowed
- ❌ **Debug files in root**: Must be in `scratch/` directory  
- ❌ **Generated output files in root**: All tool outputs (`.json`, `.csv`, etc.) belong in `scratch/` or `tests/data/` or some other subdir
- ❌ **Production code in `tools/`**: Production utilities only
- ❌ **Executable code in data directories**: Data files only

**🎯 ENHANCED FILE PLACEMENT RULES**:

**`tools/` - PRODUCTION CODE GENERATION ONLY (11 Core Tools)**:
- ✅ **Main Interface**: `main.py` - Single entry point for all tools
- ✅ **Geographic Enums**: `generate_enums.py` - Census data processing
- ✅ **WDS Enums**: `wds_enum_gen.py`, `wds_code_enum_gen.py`, `wds_productid_enum_gen.py`
- ✅ **Abbreviation System**: `abbreviations.py`, `substitution.py`, `interactive_abbreviation_manager.py`
- ✅ **Utilities**: `enum_writer.py`, `word_tracker.py`, `unified_enum_processor.py`
- ❌ **NEVER**: Demo scripts, example code, educational content
- ❌ **NEVER**: Debug scripts, investigation files, temporary analysis

**`examples/` - USER EDUCATION & DEMONSTRATIONS**:
- ✅ **Usage demonstrations**: How to use the package for real tasks
- ✅ **Educational scripts**: Teaching users package capabilities
- ✅ **Demo files**: Showcase functionality (moved from `tools/`)
- ✅ **Tutorial code**: Step-by-step examples
- ❌ **NEVER**: Production code generators, debug files

**`tests/` - VALIDATION & TESTING**:
- ✅ **Unit tests**: `test_*.py` files with pytest conventions
- ✅ **Integration tests**: API connectivity validation
- ✅ **Test utilities**: Shared testing infrastructure
- ❌ **NEVER**: Demo code, debug scripts, temporary analysis

**`tests/data/` - TEST DATA FILES ONLY**:
- ✅ **JSON data**: API responses, test fixtures
- ✅ **CSV data**: Sample datasets for testing  
- ✅ **Static files**: Configuration, schema files
- ❌ **NEVER**: Python scripts, executable code, utilities

**Key Decision Matrix**:
- Validates/asserts functionality → `tests/`
- Demonstrates usage for users → `examples/`  
- Temporary/debug/investigation → `scratch/`
- Documents the system → `docs/`
- Generates production code → `tools/`
- **Test isolation**: Each test should create its own WDS client instance
- **Test placement**: ALL tests must be placed in the `tests/` directory structure, never in root or other locations
- **Pytest compatibility**: All test files must follow pytest conventions (`test_*.py` files, `test_*` functions, pytest fixtures)
- **File Organization Guidelines**:
  - **`tests/`**: Proper unit/integration tests that validate functionality (pytest-compatible, `test_*.py` files)
  - **`examples/`**: Educational demos and usage examples for users (showcase functionality, not validate it)  
  - **`docs/`**: Official package documentation (architecture, API docs, system guides) - version controlled
  - **`scratch/`**: Debug files, temporary outputs, experimental code, session reports, and test data - NOT version controlled
  - **🚨 CRITICAL RULES - NO EXCEPTIONS 🚨**: 
    - If it validates/asserts functionality → `tests/`
    - If it demonstrates/shows usage → `examples/`
    - If it documents the package/system → `docs/` 
    - **If it's temporary/generated/debug → `scratch/` (NEVER ROOT)**
  - **Test File Naming**: Tests must be named `test_*.py` and use pytest conventions (`test_*` functions, proper fixtures)
  - **Documentation Placement**: Official docs (architecture, system guides) → `docs/`, session notes/debug reports → `scratch/`
- **Version dependencies**: Pandas 2.3+, Python 3.11+ strictly enforced in pyproject.toml
- **Modern Python Typing**: Use native Python 3.11+ type hints exclusively (project requires Python 3.11+):
  - ✅ `str | int | None` instead of `Union[str, int, None]`
  - ✅ `list[str]` instead of `List[str]`
  - ✅ `dict[str, int]` instead of `Dict[str, int]`
  - ✅ `tuple[str, ...]` instead of `Tuple[str, ...]`
  - ✅ `set[str]` instead of `Set[str]`
  - ✅ `str | None` instead of `Optional[str]`
  - ✅ `type[MyClass]` instead of `Type[MyClass]`
  - 🚨 **NEVER import Union, List, Dict, Tuple, Set, Optional, Type from typing** - use built-in generics
  - 🚨 **ALWAYS use lowercase built-in types**: `list`, `dict`, `tuple`, `set` not capitalized versions
  - 🚨 **CRITICAL RULE**: Any use of old typing imports (List, Dict, etc.) is a coding error that must be fixed immediately
- **WDS Focus Areas**: The codebase currently emphasizes:
  - **WDS Client**: `statscan/wds/client.py` - 30+ async endpoints for direct Statistics Canada API access
  - **WDS Enum Generation**: `tools/wds_*_enum_gen.py` - Real-time enum generation from WDS API data  
  - **WDS Examples**: All `examples/` should demonstrate WDS usage patterns over SDMX when possible
  - **Performance**: WDS provides simpler JSON responses vs. complex SDMX XML parsing
- **Current Repository Status**:
  - **Root**: Only `README.md` and `CHANGELOG.md` remain as official package files
  - **docs/**: Official package documentation (4 architectural guides) - version controlled
  - **examples/**: 4 usage demonstration files focusing on WDS patterns
  - **scratch/**: All temporary outputs, debug files, session reports - not version controlled
  - **tests/**: 83 pytest-compatible tests including enhanced abbreviation system validation
- **Abbreviations file maintenance**: All entries in `tools/abbreviations.py` must follow strict organizational rules:
  - **Alphabetical Order**: All sections except provinces (canonical order) must be alphabetically sorted by key
  - **No Duplicates**: Check for duplicate keys and duplicate values within substitution lists
  - **Morphological Validation**: Before adding ANY new abbreviation entry:
    1. Test if target words are already covered by existing entries using `SubstitutionEngine._generate_variants_static(existing_root)`
    2. Test if the new abbreviation key generates variants that conflict with existing explicit mappings
    3. Use `python -c "from tools.substitution import SubstitutionEngine; print(SubstitutionEngine._generate_variants_static('proposed_root'))"` to validate coverage
  - **Entry Consolidation**: When multiple related terms map to the same abbreviation:
    1. Check if they can be consolidated under a single morphological root (e.g., "employ" → ["employment", "employee", "employees"] could become just "empl": ["employ"])
    2. Verify the root generates all required variants using `_generate_variants_static()`
    3. Ensure consolidation doesn't conflict with other abbreviation entries
    4. Prefer shorter, more general roots when morphological coverage is equivalent
  - **Conflict Detection**: Flag cases where:
    1. New abbreviation values are already generated as variants of existing roots
    2. New abbreviation roots generate variants that overlap with explicit values in other entries
    3. Multiple abbreviation keys could generate the same variant terms
  - **Section Organization**: 
    - Provinces: Keep canonical order (ab, bc, mb, nb, nl, ns, nt, nu, on, pe, qc, sk, yt)
    - Other places: Alphabetical by key
    - Phrases/terms: Alphabetical by key (compound abbreviations like "copd", "gdp")
    - All others: Alphabetical by key (single-word roots for morphological extension)
  - **Quality Checks**: Always run morphological validation before accepting abbreviation changes
  - **Opportunity Analysis**: Use word tracking during enum generation to identify potential new abbreviations:
    1. Run `python tools/wds_enum_gen.py --track-words` to collect word frequency data
    2. Use `python tools/find_abbreviation_opportunities.py` for comprehensive analysis and prioritized recommendations
    3. Implement high-impact abbreviations following morphological validation procedures
    4. Validate changes with `python tools/review_abbreviations.py` before committing
