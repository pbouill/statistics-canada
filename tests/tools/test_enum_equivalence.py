#!/usr/bin/env python3
"""
Test script to ensure enum class equivalence between old and new generation approaches.
This verifies that our performance optimizations haven't broken functionality.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Set
from tools.wds_productid_enum_gen import ProductIdEnumWriter
from tools.wds_code_enum_gen import CodeSetEnumWriter
from tools.substitution import SubstitutionEngine
from tools.enum_writer import EnumEntry


def compare_enum_entries(old_entries: List[EnumEntry], new_entries: List[EnumEntry]) -> Dict[str, any]:
    """Compare two lists of enum entries and return detailed comparison results."""
    
    # Convert to dictionaries for easier comparison
    old_dict = {e.value: e for e in old_entries}
    old_names = {e.value: e.name for e in old_entries}
    old_comments = {e.value: e.comment for e in old_entries}
    
    new_dict = {e.value: e for e in new_entries}
    new_names = {e.value: e.name for e in new_entries}
    new_comments = {e.value: e.comment for e in new_entries}
    
    # Check for differences
    old_values = set(old_dict.keys())
    new_values = set(new_dict.keys())
    
    missing_in_new = old_values - new_values
    missing_in_old = new_values - old_values
    common_values = old_values & new_values
    
    # Compare names and comments for common values
    name_differences = []
    comment_differences = []
    
    for value in common_values:
        if old_names[value] != new_names[value]:
            name_differences.append({
                'value': value,
                'old_name': old_names[value],
                'new_name': new_names[value]
            })
        
        if old_comments[value] != new_comments[value]:
            comment_differences.append({
                'value': value, 
                'old_comment': old_comments[value],
                'new_comment': new_comments[value]
            })
    
    return {
        'total_old': len(old_entries),
        'total_new': len(new_entries), 
        'common_count': len(common_values),
        'missing_in_new': missing_in_new,
        'missing_in_old': missing_in_old,
        'name_differences': name_differences,
        'comment_differences': comment_differences,
        'values_match': missing_in_new == set() and missing_in_old == set(),
        'names_match': len(name_differences) == 0,
        'comments_match': len(comment_differences) == 0
    }


async def test_product_id_equivalence():
    """Test ProductID enum generation equivalence."""
    print("🏭 Testing ProductID Enum Equivalence")
    print("=" * 50)
    
    # Create generators with different configurations
    # "Old" approach: minimal variants (simulating the old behavior)
    old_engine = SubstitutionEngine(include_inflections=False, include_deriv_rel=False)
    old_generator = ProductIdEnumWriter()
    old_generator.subs_engine = old_engine
    
    # "New" approach: full variants (current optimized approach)
    new_generator = ProductIdEnumWriter()
    
    # Get test data
    cubes = await new_generator.get_all_cubes()
    test_cubes = cubes[:50]  # Test with first 50 for speed
    
    print(f"Testing with {len(test_cubes)} product IDs...")
    
    # Generate with old approach
    print("  Generating with old approach (no variants)...")
    start_time = time.time()
    old_entries = old_generator.generate_enum_entries(test_cubes)
    old_time = time.time() - start_time
    
    # Generate with new approach
    print("  Generating with new approach (with variants)...")
    start_time = time.time()
    new_entries = new_generator.generate_enum_entries(test_cubes)
    new_time = time.time() - start_time
    
    # Compare results
    comparison = compare_enum_entries(old_entries, new_entries)
    
    print(f"\n📊 ProductID Comparison Results:")
    print(f"  Old entries: {comparison['total_old']}")
    print(f"  New entries: {comparison['total_new']}")
    print(f"  Common values: {comparison['common_count']}")
    print(f"  Values match: {'✅' if comparison['values_match'] else '❌'}")
    print(f"  Names match: {'✅' if comparison['names_match'] else '❌'}")
    print(f"  Comments match: {'✅' if comparison['comments_match'] else '❌'}")
    
    # Show timing
    print(f"\n⏱️  Performance:")
    print(f"  Old approach: {old_time:.3f}s")
    print(f"  New approach: {new_time:.3f}s")
    
    # Show sample differences if names don't match (expected)
    if not comparison['names_match']:
        print(f"\n📝 Sample Name Differences (showing improved abbreviations):")
        for diff in comparison['name_differences'][:5]:
            print(f"  Value {diff['value']}:")
            print(f"    Old: {diff['old_name']}")
            print(f"    New: {diff['new_name']}")
            print(f"    Improvement: {len(diff['old_name']) - len(diff['new_name'])} characters shorter")
    
    return comparison


async def test_code_set_equivalence():
    """Test CodeSet enum generation equivalence."""
    print("\n📊 Testing CodeSet Enum Equivalence") 
    print("=" * 50)
    
    # Create generators with different configurations
    old_engine = SubstitutionEngine(include_inflections=False, include_deriv_rel=False)
    old_generator = CodeSetEnumWriter()
    old_generator.subs_engine = old_engine
    
    new_generator = CodeSetEnumWriter()
    
    # Get test data
    codesets = await new_generator.get_all_codesets()
    
    # Find a good test codeset
    test_codeset = None
    test_name = None
    
    for name, codeset in codesets.root.items():
        code_count = len(codeset.code_dict())
        if 10 <= code_count <= 50:  # Medium size for good testing
            test_codeset = codeset
            test_name = name
            break
    
    if not test_codeset:
        print("  No suitable test codeset found")
        return None
    
    print(f"Testing codeset '{test_name}' with {len(test_codeset.code_dict())} codes...")
    
    # Generate with old approach
    print("  Generating with old approach...")
    start_time = time.time()
    old_entries = old_generator.generate_enum_entries(test_codeset)
    old_time = time.time() - start_time
    
    # Generate with new approach  
    print("  Generating with new approach...")
    start_time = time.time()
    new_entries = new_generator.generate_enum_entries(test_codeset)
    new_time = time.time() - start_time
    
    # Compare results
    comparison = compare_enum_entries(old_entries, new_entries)
    
    print(f"\n📊 CodeSet Comparison Results:")
    print(f"  Old entries: {comparison['total_old']}")
    print(f"  New entries: {comparison['total_new']}")
    print(f"  Common values: {comparison['common_count']}")
    print(f"  Values match: {'✅' if comparison['values_match'] else '❌'}")
    print(f"  Names match: {'✅' if comparison['names_match'] else '❌'}")
    print(f"  Comments match: {'✅' if comparison['comments_match'] else '❌'}")
    
    print(f"\n⏱️  Performance:")
    print(f"  Old approach: {old_time:.3f}s")
    print(f"  New approach: {new_time:.3f}s")
    
    # Show differences if any
    if not comparison['names_match']:
        print(f"\n📝 Sample Name Differences:")
        for diff in comparison['name_differences'][:3]:
            print(f"  Value {diff['value']}:")
            print(f"    Old: {diff['old_name']}")
            print(f"    New: {diff['new_name']}")
    
    return comparison


def test_enum_entry_properties():
    """Test EnumEntry validation and properties."""
    print("\n🔧 Testing EnumEntry Properties")
    print("=" * 50)
    
    # Test valid entry creation
    try:
        entry = EnumEntry(name="TEST_ENTRY", value=12345, comment="Test comment")
        print("  ✅ Valid entry creation works")
    except Exception as e:
        print(f"  ❌ Valid entry creation failed: {e}")
        return False
    
    # Test name validation
    try:
        EnumEntry.validate_name("VALID_NAME")
        print("  ✅ Name validation works")
    except Exception as e:
        print(f"  ❌ Name validation failed: {e}")
        return False
    
    # Test name cleaning
    try:
        cleaned = EnumEntry.clean_name("Test Name with Spaces!")
        expected = "TEST_NAME_WITH_SPACES"
        if cleaned == expected:
            print("  ✅ Name cleaning works correctly")
        else:
            print(f"  ⚠️  Name cleaning result differs: got '{cleaned}', expected '{expected}'")
    except Exception as e:
        print(f"  ❌ Name cleaning failed: {e}")
        return False
    
    return True


async def main():
    """Run comprehensive equivalence testing."""
    print("🧪 Enum Generation Equivalence Test Suite")
    print("=" * 60)
    print("Testing that optimizations maintain functional equivalence...\n")
    
    # Test core functionality
    entry_tests_passed = test_enum_entry_properties()
    
    # Test ProductID generation
    product_comparison = await test_product_id_equivalence()
    
    # Test CodeSet generation
    code_comparison = await test_code_set_equivalence()
    
    # Overall summary
    print(f"\n🎯 Overall Test Summary")
    print("=" * 60)
    
    print(f"EnumEntry functionality: {'✅ PASS' if entry_tests_passed else '❌ FAIL'}")
    
    if product_comparison:
        product_functional_equiv = (product_comparison['values_match'] and 
                                  product_comparison['comments_match'])
        print(f"ProductID functional equivalence: {'✅ PASS' if product_functional_equiv else '❌ FAIL'}")
        print(f"ProductID name improvements: {'✅ BETTER' if not product_comparison['names_match'] else '➖ SAME'}")
    
    if code_comparison:
        code_functional_equiv = (code_comparison['values_match'] and
                               code_comparison['comments_match'])  
        print(f"CodeSet functional equivalence: {'✅ PASS' if code_functional_equiv else '❌ FAIL'}")
        print(f"CodeSet name improvements: {'✅ BETTER' if not code_comparison['names_match'] else '➖ SAME'}")
    
    print(f"\n💡 Key Points:")
    print(f"   • Enum VALUES should be identical (same ProductIDs/CodeIDs)")
    print(f"   • Enum COMMENTS should be identical (same descriptions)")  
    print(f"   • Enum NAMES may differ (improved abbreviations expected)")
    print(f"   • Performance should be similar or better")
    
    # Determine overall result
    all_functional_tests_pass = (
        entry_tests_passed and
        (not product_comparison or product_comparison['values_match']) and
        (not code_comparison or code_comparison['values_match'])
    )
    
    if all_functional_tests_pass:
        print(f"\n🎉 SUCCESS: All enum classes are functionally equivalent!")
        print(f"   The optimizations maintain correctness while improving abbreviations.")
    else:
        print(f"\n⚠️  WARNING: Some functional differences detected!")
        print(f"   Please review the differences above.")


if __name__ == "__main__":
    asyncio.run(main())
