"""
WDS Coordinate Structure Discovery Tool

This tool analyzes WDS cube structures to discover coordinate patterns,
dimensions, and static values that can be turned into enums.
"""

import asyncio
import json
from typing import Any
from dataclasses import dataclass
from collections import defaultdict
from collections import defaultdict

from statscan.wds.client import Client


@dataclass
class DimensionInfo:
    """Information about a WDS cube dimension."""
    position: int
    name: str
    members: list[dict[str, Any]]
    member_count: int
    

@dataclass
class CubeStructure:
    """Complete structure information for a WDS cube."""
    product_id: int
    title_en: str
    title_fr: str
    dimensions: list[DimensionInfo]
    total_coordinates: int
    

class WDSStructureDiscovery:
    """Tool for discovering WDS coordinate structures and creating enums."""
    
    def __init__(self):
        self.client = Client()
        self.discovered_cubes: dict[int, CubeStructure] = {}
        self.common_dimensions: dict[str, set[str]] = defaultdict(set)
        
    async def analyze_cube_structure(self, product_id: int) -> CubeStructure | None:
        """Analyze the structure of a WDS cube."""
        try:
            # Get cube metadata
            metadata = await self.client.get_cube_metadata(product_id)
            
            if not metadata or not hasattr(metadata, 'dimension'):
                print(f"❌ No metadata found for product {product_id}")
                return None
            
            print(f"✅ Analyzing product {product_id}: {getattr(metadata, 'cubeTitleEn', 'Unknown')}")
            
            dimensions = []
            total_coords = 1
            
            # Process each dimension
            for i, dim in enumerate(metadata.dimension):
                members = []
                if hasattr(dim, 'member') and dim.member:
                    for member in dim.member:
                        member_info = {
                            'id': getattr(member, 'memberId', None),
                            'name_en': getattr(member, 'memberNameEn', None),
                            'name_fr': getattr(member, 'memberNameFr', None),
                            'parent_id': getattr(member, 'parentMemberId', None),
                            'vintage': getattr(member, 'vintage', None)
                        }
                        members.append(member_info)
                        
                        # Track common dimension members
                        dim_name = getattr(dim, 'dimensionNameEn', f'Dim_{i}')
                        if member_info['name_en']:
                            self.common_dimensions[dim_name].add(member_info['name_en'])
                
                dim_info = DimensionInfo(
                    position=i,
                    name=getattr(dim, 'dimensionNameEn', f'Dimension_{i}'),
                    members=members,
                    member_count=len(members)
                )
                dimensions.append(dim_info)
                total_coords *= len(members) if members else 1
            
            cube_structure = CubeStructure(
                product_id=product_id,
                title_en=getattr(metadata, 'cubeTitleEn', ''),
                title_fr=getattr(metadata, 'cubeTitleFr', ''),
                dimensions=dimensions,
                total_coordinates=total_coords
            )
            
            self.discovered_cubes[product_id] = cube_structure
            return cube_structure
            
        except Exception as e:
            print(f"❌ Error analyzing product {product_id}: {e}")
            return None
    
    async def discover_population_cubes(self) -> list[CubeStructure]:
        """Discover and analyze population-related cubes."""
        population_product_ids = [
            98100001,  # Population estimates
            98100002,  # Census population  
            98100003,  # Census families
            98100004,  # Census households
            98100005,  # Census dwellings
            17100005,  # Population estimates, quarterly
            17100009,  # Population by age and sex
            17100139,  # Population estimates by economic region
        ]
        
        structures = []
        for pid in population_product_ids:
            structure = await self.analyze_cube_structure(pid)
            if structure:
                structures.append(structure)
                
        return structures
    
    def analyze_coordinate_patterns(self) -> dict[str, Any]:
        """Analyze patterns in discovered coordinate structures."""
        # Create containers with explicit types
        geographic_dimensions: list[dict[str, int | str]] = []
        demographic_dimensions: list[dict[str, int | str]] = []
        temporal_dimensions: list[dict[str, int | str]] = []
        common_coordinate_lengths: defaultdict[int, int] = defaultdict(int)
        dimension_name_patterns: defaultdict[str, list[dict[str, int | str]]] = defaultdict(list)
        
        patterns: dict[str, Any] = {
            'geographic_dimensions': geographic_dimensions,
            'demographic_dimensions': demographic_dimensions,
            'temporal_dimensions': temporal_dimensions,
            'common_coordinate_lengths': common_coordinate_lengths,
            'dimension_name_patterns': dimension_name_patterns
        }
        
        for cube in self.discovered_cubes.values():
            coord_length = len(cube.dimensions)
            common_coordinate_lengths[coord_length] += 1
            
            for dim in cube.dimensions:
                # Categorize dimensions by name patterns
                dim_name = dim.name.lower()
                
                if any(geo_term in dim_name for geo_term in ['geography', 'geo', 'region', 'province', 'territory']):
                    geographic_dimensions.append({
                        'product_id': cube.product_id,
                        'dimension': dim.name,
                        'position': dim.position,
                        'member_count': dim.member_count
                    })
                    
                elif any(demo_term in dim_name for demo_term in ['age', 'sex', 'gender', 'characteristics']):
                    demographic_dimensions.append({
                        'product_id': cube.product_id, 
                        'dimension': dim.name,
                        'position': dim.position,
                        'member_count': dim.member_count
                    })
                    
                elif any(time_term in dim_name for time_term in ['time', 'year', 'period', 'date']):
                    temporal_dimensions.append({
                        'product_id': cube.product_id,
                        'dimension': dim.name, 
                        'position': dim.position,
                        'member_count': dim.member_count
                    })
                
                dimension_name_patterns[dim.name].append({
                    'product_id': cube.product_id,
                    'position': dim.position,
                    'member_count': dim.member_count
                })
        
        return patterns
    
    def generate_coordinate_enum_code(self, cube: CubeStructure) -> str:
        """Generate enum code for a cube's coordinate system."""
        
        enum_name = f"Product{cube.product_id}Coordinate"
        class_name = f"Product{cube.product_id}"
        
        # Generate dimension enums
        dimension_enums = []
        for dim in cube.dimensions:
            dim_enum_name = f"{class_name}{dim.name.replace(' ', '').replace('-', '')}"
            members = []
            
            for member in dim.members[:20]:  # Limit to first 20 for practicality
                if member['name_en']:
                    # Create enum member name
                    member_name = member['name_en'].upper().replace(' ', '_').replace('-', '_')
                    member_name = ''.join(c for c in member_name if c.isalnum() or c == '_')
                    members.append(f"    {member_name} = {member['id']}  # {member['name_en']}")
            
            if members:
                dimension_enums.append(f"""
class {dim_enum_name}(Enum):
    \"\"\"{dim.name} dimension for product {cube.product_id}\"\"\"
{chr(10).join(members)}
""")
        
        # Generate coordinate builder
        coord_builder = f"""
class {enum_name}:
    \"\"\"Coordinate builder for {cube.title_en}\"\"\"
    
    @staticmethod
    def build_coordinate({', '.join(f'dim_{i}: int' for i in range(len(cube.dimensions)))}) -> str:
        \"\"\"Build a coordinate string for this cube.\"\"\"
        return "{'.'.join(f'{{dim_{i}}}' for i in range(len(cube.dimensions)))}"
        
    @staticmethod
    def get_dimensions() -> list[str]:
        \"\"\"Get dimension names in order.\"\"\"
        return {[dim.name for dim in cube.dimensions]}
"""
        
        return f"""# Generated coordinate system for product {cube.product_id}: {cube.title_en}
from enum import Enum

{chr(10).join(dimension_enums)}
{coord_builder}
"""
    
    async def save_discovery_results(self, filename: str = "wds_structure_discovery.json"):
        """Save discovery results to JSON file."""
        
        # Convert to serializable format
        results = {
            'cubes': {},
            'patterns': self.analyze_coordinate_patterns(),
            'common_dimensions': {k: list(v) for k, v in self.common_dimensions.items()}
        }
        
        for pid, cube in self.discovered_cubes.items():
            results['cubes'][str(pid)] = {
                'product_id': cube.product_id,
                'title_en': cube.title_en,
                'title_fr': cube.title_fr, 
                'total_coordinates': cube.total_coordinates,
                'dimensions': [
                    {
                        'position': dim.position,
                        'name': dim.name,
                        'member_count': dim.member_count,
                        'sample_members': dim.members[:5]  # First 5 for reference
                    }
                    for dim in cube.dimensions
                ]
            }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"📁 Discovery results saved to {filename}")


async def main():
    """Run WDS structure discovery."""
    
    print("🔍 WDS Structure Discovery Tool")
    print("=" * 40)
    
    discovery = WDSStructureDiscovery()
    
    # Discover population cube structures  
    print("\n📊 Analyzing Population Cubes:")
    print("-" * 35)
    structures = await discovery.discover_population_cubes()
    
    print(f"\n📈 Analysis Results:")
    print("-" * 20)
    print(f"✅ Discovered {len(structures)} cube structures")
    
    for cube in structures:
        print(f"\n📋 Product {cube.product_id}: {cube.title_en}")
        print(f"   📐 Dimensions: {len(cube.dimensions)}")
        print(f"   📊 Total coordinates: {cube.total_coordinates:,}")
        
        for dim in cube.dimensions:
            print(f"      • {dim.name}: {dim.member_count} members")
    
    # Analyze patterns
    patterns = discovery.analyze_coordinate_patterns()
    
    print(f"\n🔍 Coordinate Patterns:")
    print("-" * 22)
    print(f"📍 Geographic dimensions: {len(patterns['geographic_dimensions'])}")
    print(f"👥 Demographic dimensions: {len(patterns['demographic_dimensions'])}")
    print(f"📅 Temporal dimensions: {len(patterns['temporal_dimensions'])}")
    
    print(f"\n📐 Common coordinate lengths:")
    for length, count in patterns['common_coordinate_lengths'].items():
        print(f"   {length} dimensions: {count} cubes")
    
    # Generate sample enum code
    if structures:
        print(f"\n🔧 Sample Coordinate Enum (Product {structures[0].product_id}):")
        print("-" * 50)
        sample_code = discovery.generate_coordinate_enum_code(structures[0])
        print(sample_code[:1000] + "..." if len(sample_code) > 1000 else sample_code)
    
    # Save results
    await discovery.save_discovery_results("scratch/wds_structure_discovery.json")
    
    print(f"\n✨ Discovery Complete!")
    print(f"   • Run this tool to generate coordinate enum files")
    print(f"   • Results saved for further analysis")
    print(f"   • Ready to create coordinate-specific enum generators")


if __name__ == "__main__":
    asyncio.run(main())
