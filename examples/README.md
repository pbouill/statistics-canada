# Statistics Canada WDS API Examples

This directory contains **4 focused examples** plus **4 discovery/evaluation tools** that demonstrate the complete capabilities of the Statistics Canada Web Data Service (WDS) API through the `statscan` package.

## 📚 Example Structure

### 1. `basic_usage.py` - Foundation Concepts
**Start here for new users**
- WDS client initialization and basic API patterns
- Product discovery and cube metadata retrieval
- Simple coordinate-based data requests
- Working with WDS enums and response parsing
- Error handling best practices

**Run with:** `python basic_usage.py`

### 2. `demographic_analysis.py` - Real-World Use Cases
**Municipal and population analysis**
- Comprehensive demographic analysis workflows
- Saugeen Shores, Ontario case study (municipal-level analysis)
- Age, gender, and household demographic breakdowns
- Comparative analysis across geographic areas
- Practical demographic reporting patterns

**Run with:** `python demographic_analysis.py`

### 3. `geographic_discovery.py` - Location-Based Data
**Understanding Canada's geographic hierarchy**
- Product discovery by geographic focus
- Exploring cube dimensional structures
- Canada's geographic hierarchy (national → provincial → municipal)
- Building coordinates for specific locations
- Geographic coordinate validation and testing

**Run with:** `python geographic_discovery.py`

### 4. `advanced_coordinates.py` - Complex Queries
**Sophisticated statistical analysis**
- Multi-dimensional coordinate construction
- Parameter-based coordinate building
- Time series analysis with coordinate manipulation
- Complex filtering and data aggregation
- Coordinate validation and debugging techniques

**Run with:** `python advanced_coordinates.py`

## � Discovery & Evaluation Tools

### `population_evaluator.py` - Complete Pipeline Testing
**Debug and validate population data workflows**
- Test coordinates from construction to data retrieval
- Validate geographic member IDs and locations
- Debug coordinate construction issues
- Interactive mode for exploration
- Complete pipeline evaluation (523 lines of debugging power)

**Usage:**
```bash
python examples/population_evaluator.py --coordinate "2314.1.0.0.0.0.0.0.0.0" --quick
python examples/population_evaluator.py --location "Saugeen Shores"
python examples/population_evaluator.py --interactive
```

### `population_evaluator_demo.py` - Tool Demonstration
**Learn how to use the population evaluator**
- Demonstrates various evaluation scenarios
- Shows coordinate testing patterns
- Examples of common debugging workflows
- Quick reference for evaluator usage

**Run with:** `python examples/population_evaluator_demo.py`

### `wds_coordinate_discovery.py` - Structure Analysis
**Discover WDS cube coordinate patterns**
- Analyze cube dimensional structures (310 lines)
- Discover coordinate patterns across products
- Generate coordinate enum code
- Export structure analysis to JSON
- Identify common dimension patterns

**Run with:** `python examples/wds_coordinate_discovery.py`

### `wds_geographic_discovery.py` - Location Discovery
**Find valid geographic member IDs**
- Test ranges of geographic member IDs (282 lines)
- Discover major cities and populations
- Validate specific locations
- Generate geographic location enums
- Export discovery results

**Usage:**
```bash
python examples/wds_geographic_discovery.py --known
python examples/wds_geographic_discovery.py --range 1 1000
python examples/wds_geographic_discovery.py --major-cities
```

## �🚀 Getting Started

1. **Prerequisites:**
   ```bash
   # Ensure virtual environment is activated
   source .venv/bin/activate
   
   # Install package in development mode
   pip install -r requirements.dev.txt
   ```

2. **Run examples in order:**
   ```bash
   python examples/basic_usage.py           # Learn fundamentals
   python examples/demographic_analysis.py  # See real-world patterns
   python examples/geographic_discovery.py  # Understand geography
   python examples/advanced_coordinates.py  # Master complex queries
   ```

## 📖 Learning Path

**Core Examples (Start Here):**
- **New to Statistics Canada data?** → Start with `basic_usage.py`
- **Need demographic analysis?** → Go to `demographic_analysis.py`  
- **Working with geographic data?** → Use `geographic_discovery.py`
- **Building complex queries?** → Check `advanced_coordinates.py`

**Discovery & Debugging Tools:**
- **Testing coordinates/locations?** → Use `population_evaluator.py`
- **Need to understand cube structure?** → Run `wds_coordinate_discovery.py`
- **Looking for geographic member IDs?** → Try `wds_geographic_discovery.py`
- **Learning the evaluation tools?** → Start with `population_evaluator_demo.py`

## 🎯 Key Concepts Covered

- **WDS Client Usage**: Async API patterns, error handling
- **Product Discovery**: Finding relevant statistical products
- **Coordinate Systems**: Building queries for specific data subsets
- **Geographic Hierarchy**: Understanding Canada's administrative structure
- **Demographic Analysis**: Population, age/gender, household analysis
- **Time Series**: Multi-period data analysis
- **Data Validation**: Coordinate testing and debugging

## 💡 Previous Examples Consolidated

This streamlined structure replaces **17 previous example files** with **8 focused examples** (4 core + 4 discovery tools):

- **Removed duplicates**: Multiple Saugeen Shores variations → Integrated into `demographic_analysis.py`
- **Consolidated features**: Scattered demos → Organized by use case
- **Eliminated redundancy**: Overlapping functionality → Clear learning progression
- **Improved clarity**: Better documentation and error handling

Each example is self-contained but builds on concepts from previous examples, providing a clear learning path from basic usage to advanced statistical analysis.
