# Statistics Canada WDS API Examples

This directory contains examples demonstrating the Statistics Canada Web Data Service (WDS) API through the `statscan` package.

## 🌟 Featured: Smart Data Access with Fuzzy Filtering

### `fuzzy_search_demographics.py` - **START HERE** 🎯
The easiest way to get Statistics Canada data with typo-tolerant search:
- **One-line data access**: Download and filter census data in a single call
- **Typo-tolerant**: "Saugen Shore" → Saugeen Shores (automatic fuzzy matching)
- **Bilingual support**: Search in English or French
- **Full demographics**: Population, dwellings, density, and more
- **Built-in validation**: Graceful error handling for imprecise queries

**Run:** 
```bash
python fuzzy_search_demographics.py          # Quick demo (no downloads)
python fuzzy_search_demographics.py --full   # Full data extraction
```

**Example:**
```python
from statscan.wds.client import Client

client = Client()
# Get all census data for Saugeen Shores with fuzzy matching
df = await client.get_dataframe(
    product_id=98100002,  # Census subdivisions
    geo="Saugen Shore"    # Handles typos automatically!
)
# Returns: Population, dwellings, land area, and more!
```

## 🚀 Core Examples

### `cache_persistence_pattern.py` - **RECOMMENDED PATTERN** ⭐
Learn the best way to structure scripts for optimal performance:
- **Cache across contexts**: Multiple `async with Client()` blocks share cache
- **Multi-phase workflow**: Download → Analyze → Report (all using cache)
- **Production-ready**: The pattern used in real-world applications
- **Instant responses**: First call downloads, subsequent calls cached

**Run:**
```bash
python cache_persistence_pattern.py    # Run twice to see persistence!
```

**Example:**
```python
# Phase 1: Download data
async with Client(cache_path="my_cache.db") as client:
    data = await client.get_code_sets()  # Downloads (~0.2s)

# Phase 2: Analyze (uses cache!)
async with Client(cache_path="my_cache.db") as client:
    data = await client.get_code_sets()  # Cached! (~0.02s, 10x faster)

# Phase 3: Report (still uses cache!)
async with Client(cache_path="my_cache.db") as client:
    data = await client.get_code_sets()  # Still cached!
```

### `caching_performance.py` - **NEW!** Blazing Fast API Calls
Dramatically improve performance with built-in HTTP response caching:
- **Transparent caching**: All API calls automatically cached
- **Instant responses**: Repeated requests served from cache
- **Universal benefit**: DataFrames, metadata, geographic queries all cached
- **Cache management**: View stats, list cached responses, clear cache
- **Persistent or temporary**: Choose your caching strategy

**Run:**
```bash
python caching_performance.py    # Run twice to see speed difference!
```

**Example:**
```python
from statscan.wds.client import Client

# Persistent cache (recommended for repeated use)
client = Client(cache_path="census_cache.db")

# First call: downloads from API (~5 seconds)
df1 = await client.get_dataframe(98100002, geo="Toronto")

# Second call: instant from cache! (< 0.01 seconds)
df2 = await client.get_dataframe(98100002, geo="Toronto")  # 500x faster! 🚀

# Manage cache
stats = client.get_cache_stats()  # View statistics
cached = client.list_cached_responses()  # See what's cached
client.clear_cache()  # Remove all cached data
```

### `client_overview.py` - **START HERE**
Complete demonstration of the WDS Client capabilities:
- All WDS API endpoints
- Geographic location methods  
- Population data retrieval
- Search functionality
- Data format options

**Run:** `python client_overview.py`

### `basic_usage.py` - Foundation Concepts
Learn the fundamentals:
- Client initialization and configuration
- Product discovery and cube metadata
- Simple coordinate-based data requests
- WDS enums and response parsing
- Error handling patterns

**Run:** `python basic_usage.py`

### `demographic_analysis.py` - Real-World Case Study
Municipal demographic analysis using Saugeen Shores, Ontario:
- Population, age, and gender analysis
- Household and dwelling statistics
- Geographic hierarchy navigation
- Comparative demographic reporting
- DataFrame-based data processing

**Run:** `python demographic_analysis.py`

### `fuzzy_search_demographics.py` - **NEW!** Smart Location Search
Find municipalities and extract demographics using fuzzy search:
- Typo-tolerant location search ("Saugen Shore" → Saugeen Shores)
- Bilingual search support (English/French)
- Census data extraction with full table downloads
- DataFrame-based demographic analysis
- Error-handling for imprecise queries

**Run:** 
```bash
python fuzzy_search_demographics.py          # Quick demo
python fuzzy_search_demographics.py --full   # Full data extraction
```

### `geographic_discovery.py` - Location Data
Understanding Canada's geographic structure:
- Geographic hierarchy exploration (national → provincial → municipal)
- Product discovery by geographic focus
- Cube dimensional structure analysis
- Location-based coordinate building
- Geographic validation techniques

**Run:** `python geographic_discovery.py`

### `advanced_coordinates.py` - Complex Queries
Advanced statistical analysis patterns:
- Multi-dimensional coordinate construction
- Time series analysis techniques
- Complex filtering and aggregation
- Parameter-based query building
- Coordinate validation and debugging

**Run:** `python advanced_coordinates.py`

## 🔧 Discovery & Debugging Tools

### `population_evaluator.py` - Complete Pipeline Testing
Debug and validate population data workflows:
- Test coordinates from construction to data retrieval
- Validate geographic member IDs and locations
- Interactive exploration mode
- Complete pipeline evaluation

**Usage:**
```bash
python population_evaluator.py --coordinate "2314.1.0.0.0.0.0.0.0.0" --quick
python population_evaluator.py --location "Saugeen Shores"  
python population_evaluator.py --interactive
```

### `population_evaluator_demo.py` - Tool Tutorial
Learn how to use the population evaluator tool with practical examples.

### `wds_coordinate_discovery.py` - Structure Analysis
Analyze WDS cube dimensional structures:
- Discover coordinate patterns across products
- Generate dimensional analysis reports
- Export structure data to JSON

### `wds_geographic_discovery.py` - Location Discovery
Find and validate geographic member IDs:
- Test ranges of geographic identifiers
- Discover major cities and populations
- Generate geographic location mappings

**Usage:**
```bash
python wds_geographic_discovery.py --known
python wds_geographic_discovery.py --range 1 1000
python wds_geographic_discovery.py --major-cities
```

## 🏃 Quick Start

1. **Setup:**
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements/bundles/requirements.dev.txt
   ```

2. **Learning Path:**
   ```bash
   python examples/client_overview.py        # Complete overview
   python examples/basic_usage.py           # Learn fundamentals  
   python examples/demographic_analysis.py  # Real-world patterns
   python examples/geographic_discovery.py  # Geographic concepts
   python examples/advanced_coordinates.py  # Complex queries
   ```

## 📖 Key Concepts

- **WDS Client**: Single class providing all API functionality
- **Product Discovery**: Finding relevant statistical datasets  
- **Coordinate Systems**: Building queries for specific data subsets
- **Geographic Hierarchy**: Canada's administrative structure
- **Demographic Analysis**: Population and household statistics
- **Time Series**: Multi-period data analysis
- **Data Validation**: Testing and debugging techniques

Each example builds on concepts from previous examples, providing a clear progression from basic usage to advanced statistical analysis.
