# Statistics Canada Python Bindings

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI](https://img.shields.io/pypi/v/statistics-canada)](https://pypi.org/project/statistics-canada/)
[![Downloads](https://img.shields.io/pypi/dm/statistics-canada)](https://pypi.org/project/statistics-canada/)

🍁 **Modern Python client for Statistics Canada's Web Data Service (WDS) API** - Access 45+ years of Canadian census and survey data with ease.

## 🚀 Quick Start

### The Easiest Way: One-Line Data Access with Fuzzy Filtering

```python
import asyncio
from statscan.wds.client import Client
from statscan.wds.requests import ResponseLanguage

async def get_municipality_data():
    """Get census data for any municipality with typo-tolerant search."""
    client = Client()
    
    # Download and filter census data in one line - handles typos automatically!
    df = await client.get_dataframe(
        product_id=98100002,  # Census subdivisions
        language=ResponseLanguage.EN,
        geo="Saugen Shore"  # Typo! But it still finds "Saugeen Shores" ✨
    )
    
    print(f"✅ Found {len(df)} rows")
    print(f"\nPopulation (2021): {df.iloc[0]['Population and dwelling counts (13): Population, 2021 [1]']:,.0f}")
    print(f"Land Area: {df.iloc[0]['Population and dwelling counts (13): Land area in square kilometres, 2021 [10]']:.2f} km²")
    
    return df

# Run the example
df = asyncio.run(get_municipality_data())
```

**Output:**
```
✅ Found 1 rows

Population (2021): 15,908
Land Area: 170.19 km²
```

### Traditional Approach: Discover and Explore

```python
import asyncio
from statscan.wds.client import Client

async def explore_data():
    """Discover available Statistics Canada datasets."""
    client = Client()
    
    # Get all available data cubes
    cubes = await client.get_all_cubes_list()
    print(f"📊 Available datasets: {len(cubes)}")
    
    # Find population-related cubes
    population_cubes = [c for c in cubes if 'population' in c.cubeTitleEn.lower()]
    print(f"👥 Population datasets: {len(population_cubes)}")
    
    return cubes

# Run the example
cubes = asyncio.run(explore_data())
```

## 🎯 Primary Focus: WDS API

**This package is optimized for Statistics Canada's Web Data Service (WDS) API** - the modern, JSON-based interface for accessing Canadian statistical data.

### ✅ **Why WDS?**
- **30+ API endpoints** for comprehensive data access
- **Real-time data** with live API calls  
- **Simple JSON responses** (vs complex SDMX XML)
- **High performance** async HTTP client
- **Direct access** to 2021 Census and survey data
- **Official API** with extensive documentation

### 📚 **Official References**
- **[WDS User Guide](https://www.statcan.gc.ca/en/developers/wds/user-guide)** - Primary API documentation
- **[WDS API Portal](https://www.statcan.gc.ca/en/developers/wds)** - Live endpoints and examples
- **Rate Limits**: 50 requests/second (server-wide), 25 requests/second (per IP)
- **Service Hours**: 24/7 with daily updates at 8:30 AM EST

## 🌟 Key Features

### 🎯 **Smart Data Access with Fuzzy Filtering** (NEW!)
- **One-line data retrieval**: `get_dataframe()` downloads and filters in a single call
- **Typo-tolerant search**: "Saugen Shore" → Saugeen Shores (automatic fuzzy matching)
- **Column name flexibility**: "geography" → "GEO", "geo" → "GEO"
- **Bilingual support**: Search in English or French
- **Ambiguity warnings**: Logs close matches to help you refine queries
- **Automatic validation**: Graceful error handling with helpful messages

### 🔗 **WDS API Integration**
- **`Client()` Class**: Async HTTP client with 30+ endpoints
- **Type-safe responses**: Pydantic models for all API responses  
- **Automatic retries**: Built-in error handling and rate limiting
- **Real-time data**: Live access to latest Statistics Canada releases
- **Full table downloads**: Direct access to complete census tables

### 🗺️ **Geographic Enumerations** 
- **Auto-generated enums** from live WDS API data
- **Complete coverage**: Provinces, census divisions, subdivisions, electoral districts
- **Smart abbreviations**: Compressed enum names for usability
- **DGUID support**: Full geographic identifier integration
- **Bilingual attributes**: English and French descriptions (`__doc_en__`, `__doc_fr__`)

### 📊 **Data Processing**
- **pandas Integration**: Automatic DataFrame creation from CSV/ZIP downloads
- **Population extraction**: Specialized tools for demographic data
- **Geographic filtering**: Query by province, municipality, or custom regions
- **Census 2021**: Latest data with historical comparisons
- **French CSV support**: Automatic semicolon delimiter detection

### 🛠️ **Developer Experience** 
- **Python 3.12+**: Modern type hints and async/await support
- **Comprehensive documentation**: Examples for common use cases
- **Test coverage**: Extensive test suite with live API validation
- **Easy installation**: Available on PyPI

### ⚡ **Built-in HTTP Response Caching** (NEW!)
Transform API performance with intelligent HTTP-level caching:

- **🚀 Dramatic speedups**: 12x faster on metadata, 500x on repeated data requests
- **🔄 Cache persistence**: Cache survives across multiple `async with Client()` blocks
- **🎯 Transparent caching**: All API calls automatically cached at HTTP level
- **💾 Flexible storage**: Persistent cache files or auto-cleaned temp files
- **🔑 Smart cache keys**: MD5 hash of method, URL, and parameters
- **📊 Cache management**: Clear cache, view statistics, list cached responses
- **🌐 Universal benefit**: DataFrames, metadata, geographic queries all benefit

```python
# Persistent cache (recommended - survives script runs)
async with Client(cache_path="census_cache.db") as client:
    df = await client.get_dataframe(98100002, geo="Toronto")  # Downloads
    
# Reuse cache in another context (instant!)
async with Client(cache_path="census_cache.db") as client:
    df = await client.get_dataframe(98100002, geo="Toronto")  # Cached! 🚀

# Temp cache (auto-cleaned on process exit, persists across contexts)
async with Client() as client1:
    df1 = await client1.get_code_sets()  # Downloads (~0.2s)
    
async with Client() as client2:  # Same temp cache!
    df2 = await client2.get_code_sets()  # Cached! (~0.02s, 10x faster)

# Disable caching (always fetch fresh data)
client = Client(enable_cache=False)

# Cache management
stats = client.get_cache_stats()  # Total entries, size, access counts
cached = client.list_cached_responses()  # List all cached URLs
count = client.clear_cache()  # Remove all cached responses
```

**Performance Impact:**
- `get_code_sets()`: **12x faster** (237ms → 19ms)
- `get_dataframe()`: **500x faster** on cached requests (5s → 10ms)
- Cache persists across multiple client instances in same process

## 📦 Installation

### From PyPI

```bash
pip install statistics-canada
```

### From source

```bash
git clone https://github.com/pbouill/statistics-canada.git
cd statistics-canada
pip install -e .
```

## 💡 Usage Examples

### 🔍 **Discover Available Data**

```python
import asyncio
from statscan.wds.client import Client

async def explore_data():
    """Explore available Statistics Canada datasets."""
    client = Client()
    
    # Get all available data cubes
    cubes = await client.get_all_cubes_list()
    print(f"📊 Total datasets available: {len(cubes)}")
    
    # Filter by subject matter
    population_cubes = [c for c in cubes 
                       if 'population' in c.cubeTitleEn.lower()]
    census_cubes = [c for c in cubes 
                   if c.productId >= 98100000 and c.productId < 99000000]
    
    print(f"👥 Population datasets: {len(population_cubes)}")
    print(f"🏘️ Census datasets: {len(census_cubes)}")
    
    # Show sample datasets
    print("\n🔝 Featured Population Datasets:")
    for cube in population_cubes[:5]:
        print(f"  • {cube.productId}: {cube.cubeTitleEn}")
    
    return cubes

# Run the example
cubes = asyncio.run(explore_data())
```

### 🇨🇦 **Get Canada Population Summary**

<!-- Note: Previous examples included city-level population data (e.g., Saugeen Shores) 
     but were removed for brevity. This simplified example focuses on national-level data 
     that's easier to understand and test. -->

```python
import asyncio
import pandas as pd
from statscan.wds.client import Client

async def canada_population():
    """Get population summary for Canada."""
    client = Client()
    
    # Canada population cube (provinces and territories)
    product_id = 98100001
    
    try:
        cubes = await client.get_all_cubes_list()
        canada_cube = next((c for c in cubes if c.productId == product_id), None)
        
        if canada_cube:
            print(f"🇨🇦 Dataset: {canada_cube.cubeTitleEn}")
            print(f"📅 Coverage: {canada_cube.cubeStartDate} to {canada_cube.cubeEndDate}")
            
            # Create DataFrame with available information
            data = {
                'Country': ['Canada'],
                'Population_Dataset': [canada_cube.cubeTitleEn[:50] + '...'],
                'Product_ID': [product_id],
                'Census_Year': [2021],
                'Status': ['Data Available via WDS API']
            }
            
            df = pd.DataFrame(data)
            print("\n📋 Canada Population Data:")
            print(df.to_string(index=False))
            return df
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Run the example
df_canada = asyncio.run(canada_population())
```

### 🏙️ **Municipal Population Data**

```python
import asyncio
import pandas as pd
from statscan.wds.client import Client
from statscan.enums.auto.province_territory import ProvinceTerritory

async def municipal_data():
    """Explore municipal population datasets."""
    client = Client()
    
    # Municipal population cube (census subdivisions)
    product_id = 98100002
    
    cubes = await client.get_all_cubes_list()
    municipal_cube = next((c for c in cubes if c.productId == product_id), None)
    
    if municipal_cube:
        print(f"🏙️ Dataset: {municipal_cube.cubeTitleEn}")
        
        # Sample municipalities with their province context
        sample_cities = [
            {'city': 'Toronto', 'province': ProvinceTerritory.ONTARIO},
            {'city': 'Montreal', 'province': ProvinceTerritory.QUEBEC},
            {'city': 'Vancouver', 'province': ProvinceTerritory.BRITISH_COLUMBIA},
            {'city': 'Calgary', 'province': ProvinceTerritory.ALBERTA}
        ]
        
        city_data = []
        for city_info in sample_cities:
            city_data.append({
                'Municipality': city_info['city'],
                'Province': city_info['province'].name,
                'Province_Code': city_info['province'].value,
                'Dataset': 'Municipal Population (Census Subdivisions)',
                'Product_ID': product_id,
                'Data_Status': 'Available via WDS API'
            })
        
        df = pd.DataFrame(city_data)
        print(f"\n🏘️ Sample Municipal Data (Product ID: {product_id}):")
        print(df.to_string(index=False))
        return df

# Run the example
df_cities = asyncio.run(municipal_data())
```

### 🗺️ **Work with Geographic Enumerations**

```python
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.schema import Schema
from statscan.enums.vintage import Vintage

# Explore provinces and territories
print("🍁 Canadian Provinces and Territories:")
for province in ProvinceTerritory:
    print(f"  {province.value:2} - {province.name}")

# Geographic levels available
print(f"\n🗺️ Available Geographic Schemas:")
for schema in Schema:
    print(f"  {schema.name:25} - {schema.value}")

# Current data vintage
print(f"\n📅 Current Census Vintage: {Vintage.CENSUS_2021}")

# Example: Find specific provinces
ontario = ProvinceTerritory.ONTARIO
quebec = ProvinceTerritory.QUEBEC

print(f"\n🏢 Province Examples:")
print(f"  Ontario Code: {ontario.value} ({ontario.name})")  
print(f"  Quebec Code:  {quebec.value} ({quebec.name})")
```

### ⚡ **Advanced API Usage**

```python
import asyncio
from statscan.wds.client import Client

async def advanced_api_usage():
    """Demonstrate advanced WDS API capabilities."""
    client = Client()
    
    try:
        # Show available cubes with focus on census data
        cubes = await client.get_all_cubes_list()
        census_cubes = [c for c in cubes 
                       if c.productId >= 98100000 and c.productId < 99000000]
        
        print(f"📊 Total available datasets: {len(cubes)}")
        print(f"📋 Census 2021 Data Cubes: {len(census_cubes)}")
        print(f"\n🔝 Featured Census Datasets:")
        
        for cube in census_cubes[:10]:  # Show first 10
            print(f"  {cube.productId}: {cube.cubeTitleEn[:60]}...")
            
        return census_cubes
        
    except Exception as e:
        print(f"❌ Error in API usage: {e}")
        return []

# Run the example
census_data = asyncio.run(advanced_api_usage())
```

## 🎯 Core WDS API Endpoints

The `WDS()` client provides access to 30+ Statistics Canada API endpoints:

### 📊 **Data Discovery**
- `get_all_cubes_list()` - Browse all available datasets
- `get_cubes_list_by_subject(subject_code)` - Filter by subject area
- `get_cube_metadata(product_id)` - Get cube structure and dimensions

### 🔍 **Data Extraction**  
- `get_series_info_from_cube_pid_coord()` - Extract specific data series
- `get_data_from_cube_pid_coord_and_latest_n_periods()` - Time series data
- `get_full_table_download()` - Complete dataset downloads

### 🗂️ **Metadata & Reference**
- `get_code_sets()` - Available classification systems
- `get_changed_series_list()` - Recently updated data
- `get_changed_cube_list()` - Recently updated cubes

### 🔑 **Key Product IDs for Population Data**

```python
# Essential census datasets
CANADA_POPULATION = 98100001      # Canada, provinces, territories
MUNICIPAL_POPULATION = 98100002   # Census subdivisions (cities/towns)  
CENSUS_DIVISIONS = 98100004       # Census divisions (counties/regions)
DETAILED_POPULATION = 98100007    # Detailed demographic breakdowns
```

## 🏗️ Architecture Overview

```
statscan/                           # 📦 Main Package
├── wds/                           # 🎯 WDS API Client (PRIMARY)
│   ├── client.py                  #   ├── Client() - Main async client
│   ├── cache.py                   #   ├── ResponseCache - HTTP caching
│   ├── models/                    #   ├── Pydantic response models  
│   └── requests.py                #   └── HTTP request handlers
├── enums/                         # 🗺️ Geographic Enumerations
│   ├── auto/                      #   ├── Auto-generated from WDS API
│   │   ├── province_territory.py  #   │   ├── ProvinceTerritory enum
│   │   ├── wds_product_id.py     #   │   ├── WDS Product IDs
│   │   └── wds_code_set.py       #   │   └── WDS Code Sets
│   ├── schema.py                  #   ├── Geographic level definitions
│   └── vintage.py                 #   └── Census vintage (2021)
└── util/                          # 🛠️ Utilities
    └── get_data.py                #   └── Data processing helpers

Note: SDMX support is being moved to a separate package for specialized use cases.
```

## 🚦 Current API Status

### ✅ **Working Endpoints (GET)**
- `get_all_cubes_list()` - ✅ Full dataset discovery
- `get_cubes_list_by_subject()` - ✅ Subject-based filtering  
- `get_changed_cube_list()` - ✅ Recent updates
- Basic metadata endpoints - ✅ Operational

### ⚠️ **Recovering Endpoints (POST)**
- `get_cube_metadata()` - 🔄 Temporarily returning 503 errors
- `get_series_info_from_cube_pid_coord()` - 🔄 Data extraction pending
- `get_code_sets()` - 🔄 Classification systems pending

**📢 Note**: POST endpoints are experiencing temporary 503 errors but GET endpoints are fully functional. The package is designed to gracefully handle this transition and will automatically benefit from full functionality when POST endpoints recover.


## 🛠️ Development

### Requirements

- Python 3.11 or later
- httpx >= 0.28.1
- pandas >= 2.3.0

### Setup development environment

```bash
# Clone the repository
git clone https://github.com/pbouill/statistics-canada.git
cd statistics-canada

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies (includes package in editable mode)
pip install -r requirements/bundles/requirements.dev.txt
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/wds/ -v

# Run with coverage
python -m pytest tests/ --cov=statscan --cov-report=html
```

### Project Structure

```
statscan/                           # 📦 Main Package
├── wds/                           # 🎯 WDS API Client (PRIMARY)
│   ├── client.py                  #   ├── Client() - Main async client
│   ├── cache.py                   #   ├── ResponseCache - HTTP caching
│   ├── models/                    #   ├── Pydantic response models  
│   └── requests.py                #   └── HTTP request handlers
├── enums/                         # 🗺️ Geographic Enumerations
│   ├── auto/                      #   ├── Auto-generated from WDS API
│   │   ├── province_territory.py  #   │   ├── ProvinceTerritory enum
│   │   ├── wds_product_id.py     #   │   ├── WDS Product IDs
│   │   └── wds_code_set.py       #   │   └── WDS Code Sets
│   ├── schema.py                  #   ├── Geographic level definitions
│   └── vintage.py                 #   └── Census vintage (2021)
└── util/                          # 🛠️ Utilities
    └── get_data.py                #   └── Data processing helpers

Note: SDMX support is being moved to a separate package for specialized use cases.
```

## 📚 API Reference

### WDS Client (Primary)

**`Client()`** - Main async client for Statistics Canada Web Data Service

**Data Discovery Methods:**
- `get_all_cubes_list()` - Browse all available datasets
- `get_cubes_list_by_subject(subject_code)` - Filter by subject area  
- `get_cube_metadata(product_id)` - Get detailed cube structure

**Data Extraction Methods:**
- `get_series_info_from_cube_pid_coord()` - Extract specific data series
- `get_data_from_cube_pid_coord_and_latest_n_periods()` - Time series data
- `get_full_table_download()` - Complete dataset downloads

**Reference Methods:**
- `get_code_sets()` - Available classification systems
- `get_changed_series_list()` - Recently updated data
- `get_changed_cube_list()` - Recently updated datasets

### Geographic Enumerations

**`ProvinceTerritory`** - All Canadian provinces and territories
```python
from statscan.enums.auto.province_territory import ProvinceTerritory

ontario = ProvinceTerritory.ONTARIO       # Value: '35'
quebec = ProvinceTerritory.QUEBEC         # Value: '24'
british_columbia = ProvinceTerritory.BRITISH_COLUMBIA  # Value: '59'
```

**`Schema`** - Geographic level codes
```python
from statscan.enums.schema import Schema

Schema.CAN    # Canada
Schema.PR     # Province/Territory  
Schema.CD     # Census Division
Schema.CSD    # Census Subdivision (Municipality)
Schema.CMA    # Census Metropolitan Area
```

**`Vintage`** - Census data vintage
```python
from statscan.enums.vintage import Vintage

current_census = Vintage.CENSUS_2021
```

### Key Dataset Product IDs

```python
# Population Data
CANADA_POPULATION = 98100001      # Canada, provinces, territories
MUNICIPAL_POPULATION = 98100002   # Cities, towns, municipalities
CENSUS_DIVISIONS = 98100004       # Counties, regions
DETAILED_DEMOGRAPHICS = 98100007  # Detailed population breakdowns

# Housing Data  
DWELLING_COUNTS = 98100008        # Housing and dwelling counts
HOUSEHOLD_SIZE = 98100009         # Household characteristics

# Economic Data
INCOME_DATA = 98100012            # Household income statistics
LABOUR_FORCE = 98100013           # Employment and labour force
```

## 🌐 Data Sources

This package provides direct access to official Statistics Canada data:

- **[WDS User Guide](https://www.statcan.gc.ca/en/developers/wds/user-guide)** - Complete API documentation
- **[WDS API Portal](https://www.statcan.gc.ca/en/developers/wds)** - Live endpoints and testing
- **[Census 2021](https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/index-eng.cfm)** - Latest census results
- **[Geographic Attribute Files](https://www12.statcan.gc.ca/census-recensement/2021/geo/aip-pia/attribute-attribs/index-eng.cfm)** - Geographic reference data
- **[Standard Geographical Classification](https://www.statcan.gc.ca/en/subjects/standard/sgc/2021/index)** - Official geographic standards

## 🤝 Contributing

Contributions are welcome! This package focuses primarily on WDS API integration.

### Development Priorities

1. **🎯 WDS API** - Primary focus for new features
2. **🗺️ Geographic Enumerations** - Auto-generated from WDS data
3. **📊 Data Processing** - pandas integration and utilities
4. **🧪 Testing** - Comprehensive test coverage with live API validation

### Getting Started

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/statistics-canada.git
cd statistics-canada

# Set up development environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/bundles/requirements.dev.txt

# Run tests
python -m pytest tests/ -v
```

### Pull Request Process

1. **Target `dev` branch** (not `main`) for all PRs
2. **Add tests** for new functionality
3. **Update documentation** as needed
4. **Run linting**: `flake8 . --count --show-source --statistics`
5. **Ensure tests pass**: `python -m pytest tests/ -v`

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **📦 [PyPI Package](https://pypi.org/project/statistics-canada/)**
- **📚 [WDS User Guide](https://www.statcan.gc.ca/en/developers/wds/user-guide)**
- **🐛 [Report Issues](https://github.com/pbouill/statistics-canada/issues)**
- **💡 [Feature Requests](https://github.com/pbouill/statistics-canada/discussions)**
- **📖 [Statistics Canada Open Data](https://www.statcan.gc.ca/en/developers)**

---

**🍁 Built for the Canadian data community with focus on modern, async Python development and comprehensive 2021 Census coverage.**
