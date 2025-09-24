# Statistics Canada Python Bindings

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI](https://img.shields.io/pypi/dm/statistics-canada)](https://pypi.org/project/statistics-canada/)


Python bindings for the Statistics Canada Web Data Service (WDS) API, providing easy access to Canadian census data and geographic information.

## Overview

This package provides a Python interface to Statistics Canada's census data through their Web Data Service API. It includes utilities for downloading, processing, and working with Canadian census data, as well as geographic boundaries and administrative divisions.

**Key Features:**
- **WDS API Integration**: Direct access to Statistics Canada's Web Data Service API
- **Population Data Extraction**: Easy population DataFrame creation for any Canadian region
- **Geographic Enumerations**: Complete province, census division, and subdivision enums  
- **Async API Client**: High-performance async HTTP client for WDS endpoints
- **DGUID Support**: Dissemination Geography Unique Identifier utilities
- **pandas Integration**: Seamless DataFrame creation from census data
- **2021 Census Focus**: Latest census data with comprehensive geographic coverage

**Data Sources:**
- [📚 **WDS User Guide**](https://www.statcan.gc.ca/en/developers/wds/user-guide) - **Primary API Reference**
- [Statistics Canada Web Data Service](https://www.statcan.gc.ca/en/developers/wds) - Live API endpoints
- [Census geographic attribute files](https://www12.statcan.gc.ca/census-recensement/2021/ref/dict/fig/index-eng.cfm?ID=f1_1)

## Installation

### From PyPI (when available)
```bash
pip install statistics-canada
```

### From source
```bash
git clone https://github.com/pbouill/statistics-canada.git
cd statistics-canada
pip install -e .
```

## Usage

### Basic WDS API Usage

```python
import asyncio
import pandas as pd
from statscan.wds.client import Client
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.schema import Schema

# Initialize WDS client
async def basic_wds_example():
    client = Client()
    
    # Get available cubes
    cubes = await client.get_all_cubes_list()
    print(f"Available cubes: {len(cubes)}")
    
    # Work with geographic enums
    province = ProvinceTerritory.ONTARIO
    print(f"Province: {province.name}, Code: {province.value}")

# Run the example
asyncio.run(basic_wds_example())
```

### Population Data Examples

> **⚠️ Note**: These examples use the working GET endpoints while WDS POST endpoints are temporarily experiencing 503 errors. The examples show the complete workflow for when POST endpoints recover.

#### Get Canada Population Data

```python
import asyncio
import pandas as pd
from statscan.wds.client import Client

async def get_canada_population():
    """Extract population data for Canada from 2021 Census."""
    client = Client()
    
    # Population cube - Canada, provinces and territories  
    product_id = 98100001
    
    try:
        # Get cube metadata (when POST endpoints recover)
        # metadata = await client.get_cube_metadata(product_id=product_id)
        
        # For now, use available cube information
        cubes = await client.get_all_cubes_list()
        population_cube = next(
            (cube for cube in cubes if cube.productId == product_id), 
            None
        )
        
        if population_cube:
            print(f"📊 Found: {population_cube.cubeTitleEn}")
            print(f"📅 Period: {population_cube.cubeStartDate} to {population_cube.cubeEndDate}")
            
            # Create summary DataFrame
            canada_data = {
                'Geography': ['Canada'],
                'Geographic_Level': ['Country'],
                'Product_ID': [product_id],
                'Dataset': [population_cube.cubeTitleEn],
                'Census_Year': [2021],
                'Data_Available': ['Yes (via WDS API)'],
                'Status': ['Ready when POST endpoints recover']
            }
            
            df = pd.DataFrame(canada_data)
            print("\n🇨🇦 Canada Population Data Summary:")
            print(df.to_string(index=False))
            return df
        else:
            print("❌ Population cube not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Run the example
df_canada = asyncio.run(get_canada_population())
```

#### Get Saugeen Shores Population Data

```python
import asyncio
import pandas as pd
from statscan.wds.client import Client
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.schema import Schema

async def get_saugeen_shores_population():
    """Extract population data for Saugeen Shores, Ontario from 2021 Census."""
    client = Client()
    
    # Municipal population cube - Census subdivisions
    product_id = 98100002
    
    try:
        cubes = await client.get_all_cubes_list()
        municipal_cube = next(
            (cube for cube in cubes if cube.productId == product_id), 
            None
        )
        
        if municipal_cube:
            print(f"📊 Found: {municipal_cube.cubeTitleEn}")
            
            # Saugeen Shores geographic information using our enums
            province = ProvinceTerritory.ONTARIO
            schema = Schema.CSD  # Census Subdivision level
            
            # Create population data summary
            saugeen_data = {
                'Geography': ['Saugeen Shores, ON'],
                'Province': [province.name],
                'Province_Code': [province.value],
                'Geographic_Level': [schema.value],
                'Product_ID': [product_id],
                'Dataset': [municipal_cube.cubeTitleEn[:60] + '...'],
                'Census_Year': [2021],
                'DGUID_Pattern': ['2021A000535541020'],  # Expected DGUID for Saugeen Shores
                'County': ['Bruce County'],
                'Population_Estimate': ['~15,000'],  # Approximate
                'Data_Available': ['Yes (via WDS API)'],
                'Status': ['Ready when POST endpoints recover']
            }
            
            df = pd.DataFrame(saugeen_data)
            print(f"\n🏘️ Saugeen Shores Population Data Summary:")
            print(df.to_string(index=False))
            
            # Show next steps for data extraction
            print(f"\n🚀 Next Steps for Actual Data:")
            print(f"1. Use: await client.get_cube_metadata(product_id={product_id})")
            print(f"2. Find Saugeen Shores coordinates in cube dimensions")
            print(f"3. Extract data: await client.get_series_info_from_cube_pid_coord(...)")
            
            return df
        else:
            print("❌ Municipal population cube not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Run the example  
df_saugeen = asyncio.run(get_saugeen_shores_population())
```

#### Compare Multiple Regions

```python
import asyncio
import pandas as pd
from statscan.wds.client import Client
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.schema import Schema

async def compare_regional_populations():
    """Compare population data across different geographic levels."""
    client = Client()
    
    # Define regions using our enums
    regions = [
        {
            'name': 'Canada',
            'product_id': 98100001,
            'level': Schema.CAN,
            'province': None
        },
        {
            'name': 'Ontario',
            'product_id': 98100001,
            'level': Schema.PR,
            'province': ProvinceTerritory.ONTARIO
        },
        {
            'name': 'Saugeen Shores, ON',
            'product_id': 98100002,
            'level': Schema.CSD,
            'province': ProvinceTerritory.ONTARIO
        },
        {
            'name': 'Toronto, ON',
            'product_id': 98100002,
            'level': Schema.CSD,
            'province': ProvinceTerritory.ONTARIO
        }
    ]
    
    try:
        # Get available cubes
        cubes = await client.get_all_cubes_list()
        
        # Build comparison DataFrame
        comparison_data = []
        
        for region in regions:
            cube = next(
                (c for c in cubes if c.productId == region['product_id']), 
                None
            )
            
            if cube:
                comparison_data.append({
                    'Region': region['name'],
                    'Geographic_Level': region['level'].value if region['level'] else 'N/A',
                    'Province': region['province'].name if region['province'] else 'N/A',
                    'Product_ID': region['product_id'],
                    'Dataset': cube.cubeTitleEn[:50] + '...',
                    'Census_Year': 2021,
                    'Status': 'Data Available'
                })
        
        df_comparison = pd.DataFrame(comparison_data)
        print("📊 Regional Population Data Comparison:")
        print(df_comparison.to_string(index=False))
        
        return df_comparison
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Run the comparison
df_regions = asyncio.run(compare_regional_populations())
```

### Working with Geographic Enums

```python
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.schema import Schema
from statscan.enums.vintage import Vintage

# Explore available provinces
print("🍁 Available Provinces and Territories:")
for province in ProvinceTerritory:
    print(f"  {province.name}: {province.value}")

# Work with geographic schemas
print(f"\n🗺️ Available Geographic Levels:")
for schema in Schema:
    print(f"  {schema.name}: {schema.value}")

# Current census vintage
print(f"\n📅 Current Census: {Vintage.CENSUS_2021}")
```

### Available Census Years

The package supports census data from:
- 2021 (latest and currently supported)
- Additional years (2016, 2011, 2006, 2001, 1996, 1991, 1986, 1981, 1976) available through legacy CensusYear enum

### Geographic Levels

The package includes enumerations for various Canadian geographic divisions:
- **Schema**: Geographic level codes (provinces, census divisions, etc.)
- **ProvinceTerritory**: Provinces and territories with official codes
- **CensusDivision**: Census division codes
- **CensusSubdivision**: Census subdivision codes  
- **FederalElectoralDistrict**: Federal electoral district codes
- **CensusMetropolitanArea**: CMA codes
- **EconomicRegion**: Economic region codes
- And more auto-generated geographic enumerations...

## Development

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

# Install development dependencies
pip install -r requirements.dev.txt

# Install package in editable mode
pip install -e .
```

### Running Tests
```bash
# Run all tests
python -m unittest discover unittests

# Run specific test module
python -m unittest unittests.test_core
```

### Project Structure
```
statscan/                 # Main package
├── __init__.py           # Package initialization
├── _version.py           # Version information  
├── url.py                # WDS API URLs and endpoints
├── py.typed              # Type hint marker
├── wds/                  # 🎯 WDS API Client (Primary Focus)
│   ├── client.py         # Main WDS async client with 30+ endpoints
│   ├── requests.py       # HTTP request handlers
│   ├── models/           # Pydantic response models
│   └── __init__.py       # WDS module initialization
├── enums/                # Geographic enumerations
│   ├── schema.py         # Geographic level schema definitions
│   ├── vintage.py        # Current census vintage (2021)
│   ├── auto/             # Auto-generated enums from WDS API
│   │   ├── province_territory.py    # Province/territory codes
│   │   ├── census_division.py       # Census division codes  
│   │   ├── census_subdivision.py    # Census subdivision codes
│   │   ├── wds_product_id.py        # WDS Product ID enums
│   │   ├── wds_code_set.py          # WDS Code Set enums
│   │   └── ...                      # Other geographic levels
│   └── geocode/          # Geographic code utilities
├── sdmx/                 # 📊 SDMX Models (Secondary - Legacy Support)
│   ├── base.py           # Base Pydantic models
│   ├── structure.py      # SDMX structure models
│   └── ...               # SDMX data models
└── util/                 # Utility modules
    ├── get_data.py       # Data download utilities
    └── ...               # Other utilities
```

## API Reference

### WDS API Client (Primary)
- **`Client()`**: Main async client for Statistics Canada Web Data Service API
  - `get_all_cubes_list()`: Get all available data cubes  
  - `get_cube_metadata(product_id)`: Get cube structure and dimensions
  - `get_series_info_from_cube_pid_coord()`: Extract specific data series
  - 30+ endpoints following [WDS User Guide](https://www.statcan.gc.ca/en/developers/wds/user-guide)

### Geographic Enumerations  
- **`Schema`**: Geographic level codes (CAN, PR, CD, CSD, CMA, etc.)
- **`ProvinceTerritory`**: All provinces and territories with official codes
- **`CensusDivision`**: Census division codes by province
- **`CensusSubdivision`**: Census subdivision (municipality) codes
- **`Vintage`**: Current census vintage (2021)

### Population Data Access
```python
# Key Product IDs for Population Data
98100001  # Canada, provinces and territories population
98100002  # Census subdivisions (municipalities) population  
98100004  # Census divisions population
98100007  # Census divisions detailed population
```

### Data Models
- **Pydantic Models**: Type-safe response models for all WDS API endpoints
- **DataFrame Integration**: Automatic pandas DataFrame creation from API responses
- **DGUID Support**: Full support for Dissemination Geography Unique Identifiers

## Data Sources and References

This package provides access to official Statistics Canada data:

- [Web Data Service (WDS) API](https://www.statcan.gc.ca/en/developers/wds)
- [WDS User Guide](https://www.statcan.gc.ca/en/developers/wds/user-guide)
- [Census Geographic Attribute Files](https://www12.statcan.gc.ca/census-recensement/2021/geo/aip-pia/attribute-attribs/index-eng.cfm)
- [Standard Geographical Classification (SGC)](https://www.statcan.gc.ca/en/subjects/standard/sgc/2021/index)

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the GPL-3.0 License - see the LICENSE file for details.