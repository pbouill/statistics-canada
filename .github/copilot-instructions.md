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

### Advanced Automation Systems

**🤖 MULTI-REPOSITORY CHANGELOG AUTOMATION**
- **GitHub App**: `seawall-changelog-bot` with fine-grained file permissions (CHANGELOG.md, changelog.md only)
- **Workflow**: `.github/workflows/dev-changelog.yml` uses GitHub Contents API for secure file operations
- **Authentication**: Uses GitHub App tokens (no personal access tokens needed)
- **Multi-repo Ready**: Generic workflow design with configurable repository secrets
- **Key Innovation**: API-based approach bypasses git command permission issues with file-specific GitHub Apps
- **Status**: ✅ FULLY OPERATIONAL - automatically updates changelogs on PR merge to dev branch

**🚀 ENHANCED RELEASE PIPELINE ARCHITECTURE (SEPTEMBER 2025)**
- **📚 DOCUMENTATION**: `/docs/charts/` - Comprehensive visual documentation with Mermaid flowcharts
- **Phase 1 - Smart Changelog (🟢 ACTIVE)**: `.github/workflows/dev-changelog.yml`
  - Intelligent file filtering: Package vs infrastructure changes (60-80% efficiency gain)
  - GitHub App integration: `seawall-changelog-bot` for secure commits
  - File patterns: `statscan/`, `pyproject.toml`, `requirements*.txt` → trigger; `.github/`, `docs/`, `tools/` → skip
- **Phase 2 - Complete Pipeline (🟠 READY)**: `.github/workflows/release-pipeline-new.yml`
  - 5-stage automation: Detection → Build → Changelog → PyPI → GitHub Release
  - Automatic version extraction from wheel filenames
  - Comprehensive rollback mechanisms with changelog state management
- **Phase 3 - Shared QA/QC (🔵 PROPOSED)**: `.github/workflows/qa-qc-checks.yml`
  - Reusable workflow eliminating code duplication
  - Configurable builds: `build-required: false` (PRs) vs `true` (releases)
- **Visual Documentation**: Interactive Mermaid diagrams with color-coded status tracking
- **Migration Tools**: `./scratch/migrate_release_pipeline.sh` for safe phase deployment
- **Testing Framework**: `./scratch/test_release_pipeline.sh` for validation scenarios
- **Branch Flow**: `dev` → changelog filtering → `main` → 5-stage pipeline → PyPI + GitHub release

### Directory Layout ###
- **`debug/`**: Debugging tools and scripts
- **`docs/`**: Documentation files
  - **`docs/charts/`**: 🎨 **VISUAL DOCUMENTATION HUB** - Interactive pipeline diagrams and architecture charts
    - `workflow_diagram.md`: Mermaid flowchart with color-coded workflow status
    - `enhanced_release_pipeline.md`: Complete architecture with file cross-references
    - `implementation_summary.md`: Current phase status and deployment timeline
    - `README.md`: Navigation guide for visual documentation
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

#### Enhanced Test Organization Structure
**🎯 NEW IMPROVED TEST ARCHITECTURE**:

**`tests/` - Root Directory**:
- **`conftest.py`**: Central fixture imports for both WDS and SDMX fixtures
- **`fixtures.py`**: Enhanced fixture system with raw response data and specialized extractors
- **`test_fixture_paths.py`**: Centralized StrEnum classes for file path management

**`tests/wds/` - WDS API Testing**:
- **`test_network_fixtures.py`**: **NETWORK-BASED TESTS** that generate fixtures for subsequent tests
  - Makes live WDS API calls to generate test data
  - Saves both raw httpx responses AND processed data
  - Uses `TestFixtureManager` for consistent file naming and metadata
  - Must run FIRST to generate fixtures for other tests
- **`test_end_user_functionality.py`**: Advanced functionality tests using generated fixtures
  - Uses specialized extraction fixtures (e.g., `wds_individual_code_set_scalar`)
  - Tests DataFrame conversion, filtering, and real-world usage patterns
  - Can run WITHOUT network access using fixture data

**`tests/sdmx/` - SDMX Testing (Secondary Priority)**:
- **`test_network_fixtures.py`**: Minimal SDMX fixture generation (mostly uses existing data)
- **`test_end_user_functionality.py`**: SDMX parsing and compatibility tests

**`tests/data/` - Organized Test Data**:
- **`tests/data/wds/`**: WDS-specific test fixtures
  - `raw_*.json`: Complete httpx responses with metadata
  - `*.json`: Processed data for end-user testing
- **`tests/data/sdmx/`**: SDMX-specific test fixtures

#### Advanced Fixture System
**🚀 ENHANCED FIXTURE ARCHITECTURE**:

**Raw Response Fixtures**: Store complete httpx responses with metadata
- `wds_raw_code_sets`: Raw API response with httpx metadata
- `wds_raw_cubes_list`: Raw cubes list with full API context
- `wds_raw_cube_metadata`: Raw cube metadata with request parameters

**Processed Data Fixtures**: Clean data optimized for end-user testing
- `wds_processed_code_sets`: Clean code sets without httpx metadata
- `wds_processed_cubes_list`: Sample cubes list for testing

**Specialized Extraction Fixtures**: Extract specific data for model testing
- `wds_individual_code_set_scalar`: Just scalar codes for individual model tests
- `wds_cube_basic_info`: Basic cube information extraction
- `wds_census_cubes_only`: Filtered census cubes (productId 98xxx)
- `wds_population_cubes_only`: Population-related cubes only

**Path Management**: 
- **`TestFixturePaths`**: StrEnum classes (`WDSFixturePaths`, `SDMXFixturePaths`) manage file naming
- **`TestFixtureManager`**: Utility class for saving/loading fixtures with metadata
- **Templated paths**: Support parameterized filenames (e.g., `cube_metadata_{product_id}.json`)

#### Test Execution Workflow
**CRITICAL EXECUTION ORDER**:
1. **Network Tests First**: Run `tests/*/test_network_fixtures.py` to generate raw data
2. **Functionality Tests**: Run `tests/*/test_end_user_functionality.py` using generated fixtures
3. **Advanced Tests**: Can pull from existing fixtures without network calls

**Test Markers**:
- **`@pytest.mark.network`**: Requires internet access, generates fixtures
- **`@pytest.mark.asyncio`**: Async test methods for WDS client calls
- **Integration Tests**: Network tests that require live API access

**Legacy Compatibility**: `python tests/run_tests.py` provides unittest fallback but new tests should be pure pytest

#### Test Isolation and Best Practices
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

### CLI Tools Organization
**Critical**: Tool organization follows a strict separation between core functionality and CLI interfaces:
- **`tools/`**: Core classes, modules, and data processing utilities (9 core components)
  - Enum writer classes (`wds_*_enum_gen.py`)
  - Core functionality (`word_tracker.py`, `substitution.py`, `abbreviations.py`)
  - Data processing (`generate_enums.py`, `wds_coordinate_discovery.py`)
  - Supporting modules (`enum_writer.py`)
- **`tools/cli/`**: Command-line interfaces and interactive tools (4 CLI scripts)
  - Entry point (`main.py`)
  - WDS CLI interface (`wds_enum_gen.py`)
  - Interactive tools (`interactive_abbreviation_manager.py`)
  - Batch processors (`unified_enum_processor.py`)
- **Design Principle**: CLI scripts **use** core classes but contain no business logic themselves
- **Import Pattern**: CLI scripts import from parent `tools/` directory: `from tools.wds_code_enum_gen import CodeSetEnumWriter`

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
- **`tools/cli/interactive_abbreviation_manager.py`**: Enhanced interactive system for adding new abbreviations and applying consolidation opportunities
- **`tools/cli/unified_enum_processor.py`**: Single entry point for processing all enum types with consistent word tracking
- **Morphological Extension**: Root words like "empl" automatically cover "employ", "employment", "employed", "employees", etc.
- **Testing Coverage**: Use `SubstitutionEngine._generate_variants_static("word")` to test morphological coverage before adding new abbreviations
- **Performance Impact**: Proper abbreviations reduce enum identifier length from 150+ chars to manageable names
- **Word Tracking Workflow**: 
  1. Run `python tools/cli/unified_enum_processor.py --track-words` to collect word frequency data across all generators
  2. Use `python tools/find_abbreviation_opportunities.py` for comprehensive analysis with smart suggestions
  3. Run `python tools/cli/interactive_abbreviation_manager.py` for user-friendly abbreviation selection and implementation
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

**`tools/` - CORE CLASSES AND MODULES (9 Core Tools)**:
- ✅ **Geographic Enums**: `generate_enums.py` - Census data processing
- ✅ **WDS Enum Classes**: `wds_code_enum_gen.py`, `wds_productid_enum_gen.py` - Core enum writer classes
- ✅ **Abbreviation System**: `abbreviations.py`, `substitution.py` - Core functionality
- ✅ **Utilities**: `enum_writer.py`, `word_tracker.py`, `wds_coordinate_discovery.py` - Supporting modules
- ❌ **NEVER**: CLI scripts, interactive tools, command-line interfaces
- ❌ **NEVER**: Demo scripts, example code, educational content
- ❌ **NEVER**: Debug scripts, investigation files, temporary analysis

**`tools/cli/` - COMMAND-LINE INTERFACE SCRIPTS (4 CLI Tools)**:
- ✅ **Main CLI Interface**: `main.py` - Entry point for all CLI operations
- ✅ **WDS CLI**: `wds_enum_gen.py` - Command-line interface for WDS enum generation
- ✅ **Interactive Tools**: `interactive_abbreviation_manager.py` - User-facing interactive systems
- ✅ **Batch Processors**: `unified_enum_processor.py` - Automated workflow scripts
- ❌ **NEVER**: Core classes or business logic (belongs in parent `tools/`)
- ❌ **NEVER**: Demo code, debug scripts, temporary analysis

**`examples/` - USER EDUCATION & DEMONSTRATIONS**:
- ✅ **Usage demonstrations**: How to use the package for real tasks
- ✅ **Educational scripts**: Teaching users package capabilities
- ✅ **Demo files**: Showcase functionality (moved from `tools/`)
- ✅ **Tutorial code**: Step-by-step examples
- ❌ **NEVER**: Production code generators, debug files

**`tests/` - VALIDATION & TESTING**:
- ✅ **Unit tests**: `test_*.py` files with pytest conventions
- ✅ **Integration tests**: API connectivity validation with `@pytest.mark.network`
- ✅ **Test utilities**: Enhanced fixture system with `TestFixtureManager`
- ✅ **Path management**: `test_fixture_paths.py` with StrEnum classes
- ✅ **Network fixtures**: Generate raw httpx responses and processed data
- ✅ **Specialized extractors**: Individual model testing fixtures
- ❌ **NEVER**: Demo code, debug scripts, temporary analysis

**`tests/data/` - ORGANIZED TEST FIXTURES**:
- ✅ **`wds/`**: WDS-specific fixtures with `raw_*.json` and processed data
- ✅ **`sdmx/`**: SDMX-specific test fixtures (secondary priority)
- ✅ **JSON metadata**: Each fixture includes `_test_metadata` for tracking
- ✅ **Response simulation**: Raw fixtures include `httpx_metadata`
- ❌ **NEVER**: Python scripts, executable code, utilities

**Key Decision Matrix**:
- Validates/asserts functionality → `tests/`
- Demonstrates usage for users → `examples/`  
- Temporary/debug/investigation → `scratch/`
- Documents the system → `docs/`
- Generates/cleans production code → `tools/`
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

## 🚨 **CRITICAL TYPING REQUIREMENTS - PYTHON 3.11+ ONLY** 🚨

**ABSOLUTE REQUIREMENT**: ALL code must use modern Python 3.11+ native type annotations. Legacy typing imports are FORBIDDEN.

### ✅ **REQUIRED MODERN SYNTAX (Python 3.11+)**:
```python
# Built-in generics (PEP 585) - REQUIRED
list[str]                    # ✅ CORRECT
dict[str, int]              # ✅ CORRECT  
tuple[str, ...]             # ✅ CORRECT
set[str]                    # ✅ CORRECT
type[MyClass]               # ✅ CORRECT

# Union types (PEP 604) - REQUIRED
str | int                   # ✅ CORRECT
str | None                  # ✅ CORRECT
dict[str, Any] | None       # ✅ CORRECT
list[dict[str, Any]]        # ✅ CORRECT

# Reduced typing imports
from typing import Any      # ✅ Only when needed
```

### 🚫 **FORBIDDEN LEGACY SYNTAX (Python 3.8-3.10)**:
```python
# Legacy typing imports - FORBIDDEN
from typing import List, Dict, Tuple, Set, Union, Optional, Type  # 🚫 NEVER

# Legacy syntax patterns - FORBIDDEN
List[str]                   # 🚫 WRONG - use list[str]
Dict[str, int]             # 🚫 WRONG - use dict[str, int]
Tuple[str, ...]            # 🚫 WRONG - use tuple[str, ...]
Set[str]                   # 🚫 WRONG - use set[str]
Union[str, int]            # 🚫 WRONG - use str | int
Optional[str]              # 🚫 WRONG - use str | None
Type[MyClass]              # 🚫 WRONG - use type[MyClass]
```

### � **MIGRATION EXAMPLES**:
```python
# OLD (forbidden) → NEW (required)
def old_function(items: List[Dict[str, Any]]) -> Optional[str]:  # 🚫 WRONG
def new_function(items: list[dict[str, Any]]) -> str | None:     # ✅ CORRECT

# OLD (forbidden) → NEW (required)  
data: Dict[str, Union[int, str]] = {}                          # � WRONG
data: dict[str, int | str] = {}                                # ✅ CORRECT

# OLD (forbidden) → NEW (required)
from typing import List, Dict, Optional                         # 🚫 WRONG
# Only import what's actually needed from typing:
from typing import Any                                          # ✅ CORRECT
```

### 🚨 **ENFORCEMENT RULES**:
- **Linting Error**: Any use of `List`, `Dict`, `Union`, `Optional`, etc. from typing is a linting error that MUST be fixed immediately
- **Code Review**: All PRs will be rejected if they contain legacy typing syntax
- **CI/CD**: Automated checks prevent legacy typing from being merged
- **Zero Tolerance**: No exceptions - the project requires Python 3.11+ so we must use modern syntax exclusively
- **Auto-Fix Command**: Use modern type annotations in all new code and fix any legacy patterns found during linting
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
    1. Run `python tools/cli/wds_enum_gen.py --track-words` to collect word frequency data
    2. Use `python tools/find_abbreviation_opportunities.py` for comprehensive analysis and prioritized recommendations
    3. Implement high-impact abbreviations following morphological validation procedures
    4. Validate changes with `python tools/review_abbreviations.py` before committing

## 🔧 **DOCUMENTATION MAINTENANCE & AI AGENT ASSUMPTIONS**

### **CRITICAL: Self-Maintaining Documentation System**
**📚 AGENT MEMORY PRINCIPLE**: This file serves as maintained memory for new AI chat sessions. When system architecture, workflows, or approaches change, **UPDATE THIS FILE IMMEDIATELY** to ensure future agents have accurate context.

### **Visual Documentation Reference (MANDATORY)**
**🎨 PIPELINE CHARTS**: When working with GitHub Actions/workflows, **ALWAYS reference and maintain** visual documentation:
- **Primary Reference**: `/docs/charts/workflow_diagram.md` - Interactive Mermaid flowchart
- **Architecture Details**: `/docs/charts/enhanced_release_pipeline.md` - Complete system overview
- **Implementation Status**: `/docs/charts/implementation_summary.md` - Current phase status
- **Navigation Guide**: `/docs/charts/README.md` - Quick access to all components

### **AI Agent Solution Development Protocol**
**🤖 ASSUMPTION TRANSPARENCY**: When developing solutions, agents MUST:

1. **State Information Sources**: Explicitly mention when solution approaches come from copilot-instructions.md
2. **Reference Visual Charts**: Link to relevant `/docs/charts/` files when discussing workflows/architecture
3. **Validate Current Status**: Check phase implementation status (🟢 Active, 🟠 Ready, 🔵 Proposed) before making changes
4. **Update Documentation**: When implementing new systems, update BOTH code AND visual documentation
5. **Cross-Reference Files**: Ensure Mermaid diagrams reflect actual workflow filenames and current architecture

### **Documentation Update Triggers**
**⚡ IMMEDIATE UPDATE REQUIRED** when changes involve:
- **Workflow files** (`.github/workflows/*.yml`) - Update charts and status indicators
- **Architecture changes** - Update Mermaid diagrams and cross-references  
- **Release pipeline modifications** - Update phase status and implementation timelines
- **New automation systems** - Add to advanced automation sections
- **Directory structure changes** - Update directory layout section
- **Testing framework updates** - Update testing strategy sections

### **Color-Coded Status System**
**🎨 VISUAL STATUS INDICATORS** (maintain consistency across all documentation):
- 🟢 **Active** (Green) - Currently deployed and operational
- 🟠 **Ready** (Orange) - Implemented, awaiting deployment
- 🔵 **Proposed** (Blue) - Planned enhancement, ready for integration
- ⚪ **Legacy** (Gray) - Deprecated, maintained for rollback

### **Agent Handoff Protocol**
**🔄 SESSION CONTINUITY**: When completing tasks, agents should:
1. **Update Implementation Status**: Change phase indicators (🔵 → 🟠 → 🟢) as appropriate
2. **Document Decisions**: Add rationale for architectural choices to maintain context
3. **Update Visual Charts**: Ensure Mermaid diagrams reflect current implementation
4. **Note Testing Status**: Update testing framework and validation procedures
5. **Flag Dependencies**: Highlight any prerequisite steps for future phases

## 🤖 **ADVANCED CHANGELOG AUTOMATION SYSTEM**

### **GitHub App Architecture (seawall-changelog-bot)**

**✅ FULLY OPERATIONAL MULTI-REPOSITORY SYSTEM**:
- **GitHub App Name**: `seawall-changelog-bot` 
- **Permissions**: Contents (read/write for CHANGELOG.md, changelog.md), Pull requests (read), Metadata (read)
- **Authentication**: Uses GitHub App installation tokens (no PATs required)
- **Security**: Fine-grained permissions limited to specific files only
- **Multi-repo Ready**: Generic secrets (`CHANGELOG_BOT_APP_ID`, `CHANGELOG_BOT_PRIVATE_KEY`)

### **Workflow Implementation**

**🚀 KEY INNOVATION - GitHub Contents API Approach**:
```yaml
# .github/workflows/dev-changelog.yml
- name: Check for changes and update via GitHub API
  uses: actions/github-script@v7
  with:
    github-token: ${{ steps.app-token.outputs.token }}
    script: |
      // Uses github.rest.repos.createOrUpdateFileContents instead of git commands
      // This works with fine-grained file-specific permissions
```

**🔧 TECHNICAL DETAILS**:
- **Trigger**: Merged PRs to `dev` branch (and other development branches)
- **Process**: Generate changelog locally → Upload via GitHub Contents API
- **Bypass**: GitHub App has branch protection bypass permissions
- **Identity**: Commits as `seawall-changelog-bot[bot]` with proper attribution

### **Troubleshooting Guide**

**❌ COMMON ISSUE: PR Comment Permission Errors**:
```
RequestError [HttpError]: Resource not accessible by integration
x-accepted-github-permissions: 'issues=write; pull_requests=write'
```

**🔍 ROOT CAUSE ANALYSIS**:
1. **Permission Propagation Delay**: GitHub App permission changes can take 5-10 minutes to propagate
2. **Installation Scope**: App needs to be installed with Issues: Write permission for PR comments
3. **Fine-grained vs Repository**: File-specific permissions may conflict with Issues API requirements

**🛠️ TROUBLESHOOTING STEPS**:
1. **Verify App Installation**: Check GitHub App is properly installed on repository
2. **Check Permissions**: Ensure GitHub App has `Issues: Write` permission (not just Contents)
3. **Wait for Propagation**: Allow 10+ minutes after permission changes
4. **Re-run Workflow**: Use `mcp_github_rerun_workflow_run` to test updated permissions
5. **Manual Test**: Create test PR and merge to trigger workflow

**✅ CURRENT STATUS**:
- **Core Functionality**: ✅ Working (changelog updates successfully)
- **GitHub Contents API**: ✅ Working (file commits successful)  
- **Branch Protection Bypass**: ✅ Working (commits bypass protection)
- **PR Commenting**: ⚠️ Optional feature - requires broader permissions

**💡 FUTURE ENHANCEMENTS**:
- **Self-contained Script**: Embed changelog logic directly in workflow (no external scripts)
- **Permission Optimization**: Minimize required permissions for maximum security
- **Multi-file Support**: Extend to other automated file updates (version bumps, documentation)
- **Release Integration**: Auto-generate release notes from changelog entries
