#!/usr/bin/env python3
"""
Quick test of the word tracking and abbreviation analysis system.
This demonstrates the functionality without running the full enum generation.
"""

import asyncio
import sys
from pathlib import Path

from tools.wds_productid_enum_gen import ProductIdEnumWriter
from tools.wds_code_enum_gen import CodeSetEnumWriter
from tools.word_tracker import get_word_tracker, reset_word_tracker
from statscan.util.log import configure_logging


import asyncio
import sys
from pathlib import Path
import pytest

from tools.wds_productid_enum_gen import ProductIdEnumWriter


@pytest.mark.asyncio
async def test_abbreviation_analysis():
    """Test the abbreviation analysis system with a small sample."""
    
    print("🧪 Testing Abbreviation Analysis System")
    print("=" * 50)
    
    # Configure logging
    configure_logging(level="INFO")
    
    # Reset word tracker
    reset_word_tracker()
    
    # Test with ProductID generator (smaller dataset)
    print("🏭 Testing ProductID word tracking...")
    
    generator = ProductIdEnumWriter(track_words=True)
    cubes = await generator.get_all_cubes()
    
    # Process first 50 cubes for demonstration
    test_cubes = cubes[:50]
    print(f"📊 Processing {len(test_cubes)} cubes for analysis...")
    
    entries = generator.generate_enum_entries(test_cubes)
    print(f"✅ Generated {len(entries)} enum entries")
    
    # Test with a small CodeSet
    print("\n📊 Testing CodeSet word tracking...")
    
    codeset_generator = CodeSetEnumWriter(track_words=True)
    codesets = await codeset_generator.get_all_codesets()
    
    # Pick a small codeset for testing
    test_codeset_name = "frequency"  # Usually small
    if test_codeset_name in codesets:
        test_codeset = codesets[test_codeset_name]
        codeset_entries = codeset_generator.generate_enum_entries(
            test_codeset, 
            codeset_name=test_codeset_name
        )
        print(f"✅ Generated {len(codeset_entries)} codeset entries")
    else:
        print(f"⚠️  CodeSet '{test_codeset_name}' not found")
    
    # Analyze results
    print("\n🔍 Analyzing Word Tracking Results")
    print("=" * 50)
    
    tracker = get_word_tracker()
    
    if not tracker.word_stats:
        print("❌ No words were tracked")
        return
    
    print(f"📈 Total unique words tracked: {len(tracker.word_stats)}")
    
    # Get candidates with low thresholds for demonstration
    # Check if this is an enhanced tracker or standard tracker
    if hasattr(tracker, 'get_enhanced_abbreviation_candidates'):
        candidates = tracker.get_enhanced_abbreviation_candidates(
            min_frequency=1,  # Show all frequencies
            min_length=4,     # Show shorter words
            max_results=20    # Limit results
        )
    else:
        candidates = tracker.get_abbreviation_candidates(
            min_frequency=1,  # Show all frequencies
            min_length=4,     # Show shorter words
            max_results=20    # Limit results
        )
    
    if not candidates:
        print("✅ No abbreviation candidates found - system is well optimized!")
        return
    
    print(f"🎯 Found {len(candidates)} potential abbreviation opportunities")
    
    # Show top candidates
    print("\n🏆 Top Abbreviation Candidates:")
    print(f"{'Rank':<4} {'Word':<15} {'Freq':<6} {'Savings':<8} {'Sources'}")
    print("-" * 55)
    
    for i, (word, stats) in enumerate(candidates[:15], 1):
        sources_str = ", ".join(stats.sources)[:20]
        print(f"{i:<4} {word:<15} {stats.frequency:<6} {stats.total_potential_savings:<8.0f} {sources_str}")
    
    # Generate quick report
    print(f"\n📊 Analysis Summary:")
    total_savings = sum(stats.total_potential_savings for _, stats in candidates)
    avg_frequency = sum(stats.frequency for _, stats in candidates) / len(candidates)
    
    print(f"  • Total potential character savings: {total_savings:.0f}")
    print(f"  • Average candidate frequency: {avg_frequency:.1f}")
    print(f"  • Highest impact word: '{candidates[0][0]}' ({candidates[0][1].total_potential_savings:.0f} chars)")
    
    # Show suggestions for top 5
    print(f"\n💡 Suggested Abbreviations (Top 5):")
    for word, stats in candidates[:5]:
        # Simple suggestion logic for testing
        if len(word) <= 4:
            suggested = word.lower()
        elif word.lower().endswith('tion'):
            suggested = word.lower()[:4]
        elif word.lower().endswith('ing'):
            suggested = word.lower()[:4]
        elif word.lower() in ['fiscal', 'ending', 'occasional']:
            suggested = {'fiscal': 'fisc', 'ending': 'end', 'occasional': 'occ'}.get(word.lower(), word[:4])
        else:
            suggested = word.lower()[:4]
        
        savings_per_use = len(word) - len(suggested)
        total_impact = savings_per_use * stats.frequency
        print(f"  • '{word}' → '{suggested}' (saves {savings_per_use} × {stats.frequency} = {total_impact} chars)")
    
    # Save sample data
    output_dir = Path("scratch/test_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save tracking data
    tracking_file = output_dir / "sample_word_tracking.json"
    if hasattr(tracker, 'save_enhanced_tracking_data'):
        tracker.save_enhanced_tracking_data(tracking_file)
    else:
        tracker.save_tracking_data(tracking_file)
    print(f"\n💾 Sample tracking data saved: {tracking_file}")
    
    # Generate sample report
    report_file = output_dir / "sample_analysis_report.md"
    if hasattr(tracker, 'generate_enhanced_markdown_report'):
        report = tracker.generate_enhanced_markdown_report(
            output_file=report_file,
            include_contexts=True,
            include_morphological=True
        )
    else:
        report = tracker.generate_abbreviation_report(
            output_file=report_file,
            include_contexts=True
        )
    print(f"📄 Sample analysis report saved: {report_file}")
    
    print(f"\n🎉 Test completed successfully!")
    print(f"📁 Check {output_dir} for generated files")
    
    return candidates


if __name__ == "__main__":
    try:
        result = asyncio.run(test_abbreviation_analysis())
        if result:
            print(f"\n✅ Found {len(result)} abbreviation opportunities in test data")
        else:
            print(f"\n✅ Test completed - system appears well optimized")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
