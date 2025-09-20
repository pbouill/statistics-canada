# Statistics Canada WDS API Examples

This directory contains examples demonstrating the Statistics Canada Web Data Service (WDS) API through the `statscan` package.

## 🚀 Core Examples

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
   pip install -r requirements.dev.txt
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
