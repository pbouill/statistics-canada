# Statistics Canada Python Bindings - AI Coding Instructions

## Architecture Overview

This is a Python package providing bindings for Statistics Canada's Web Data Service (WDS) API and census data processing. The architecture follows a layered approach:

### Core Components
- **`statscan/wds/`**: Main WDS API client with async HTTP operations (`client.py` contains the `WDS` class)
- **`statscan/enums/`**: Hierarchical geographic enumerations with auto-generated code from census data
- **`statscan/sdmx/`**: SDMX (Statistical Data and Metadata eXchange) data models using Pydantic
- **`statscan/util/`**: Data download/processing utilities with async operations
- **`tools/generate_enums.py`**: Code generation system for geographic enumerations

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
- **`scratch/`**: Scratchpad for experimentation


### Data Flow Architecture
1. **API Layer**: `WDS` class in `client.py` provides async methods matching WDS endpoints
2. **Model Layer**: Pydantic models in `sdmx/` handle response serialization/validation
3. **Enum Layer**: Auto-generated geographic enums in `enums/auto/` with parent classes in `enums/geocode/`
4. **Utility Layer**: `util/get_data.py` handles file downloads and DataFrame operations

## Development Workflows

### Environment Setup
```bash
# Python 3.11+ required - check pyproject.toml for version constraints
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.dev.txt  # Installs package in editable mode via -e .
```

### Testing Strategy
- **Primary**: Use `python -m pytest tests/ -v` for running tests
- **Fallback**: `python tests/run_tests.py` provides unittest compatibility
- **Integration**: Tests require internet access for WDS API calls
- **Async Testing**: Uses `pytest-asyncio` for async test methods

### Code Generation Workflow
**Critical**: Geographic enumerations are auto-generated from Statistics Canada data:
```bash
python tools/generate_enums.py  # Downloads census data and regenerates enums/auto/ files
```
- Never manually edit files in `statscan/enums/auto/` - they are overwritten
- Modify templates in `tools/generate_enums.py` and parent classes in `enums/geocode/`
- Uses pandas to process census CSV data and generates Enum classes with proper inheritance

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
- **WDS URL**: Base URL in `statscan/url.py` as `WDS_URL`
- **Geographic Data**: Downloads from `GEO_ATTR_FILE_2021_URL` for enum generation
- **Response Format**: All WDS responses have `{"status": "SUCCESS", "object": {...}}` structure

### MCP Server
- **`statscan/mcp_server.py`**: Model Context Protocol server for AI integration
- **Resources**: Exposes WDS requests, version info, and code sets via MCP
- **Usage**: Run with `python -m statscan.mcp_server` for AI tool integration

## Critical Development Notes

- **Never commit** auto-generated files in `statscan/enums/auto/` to git
- **Always use absolute imports** within the package (e.g., `from statscan.enums.schema import Schema`)
- **Async contexts required** for WDS client operations - don't use sync patterns
- **Geographic codes follow DGUID format**: `{Year:4}{Schema:5}{Province:2}{Identifier:N}`
- **Test isolation**: Each test should create its own WDS client instance
- **Version dependencies**: Pandas 2.3+, Python 3.11+ strictly enforced in pyproject.toml
