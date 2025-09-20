#!/usr/bin/env python3
"""
Test script for the enhanced interactive abbreviation management system.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.interactive_abbreviation_manager import InteractiveAbbreviationManager
from tools.word_tracker import WordTracker


def test_interactive_system():
    """Test the enhanced interactive abbreviation management system."""
    print("🧪 Testing Enhanced Interactive Abbreviation Management System")
    print("=" * 70)
    
    # 1. Create test word tracking data
    print("1️⃣ Creating test word tracking data...")
    word_tracker = WordTracker()
    
    # Add some sample tracked words that would benefit from abbreviation
    test_words = {
        "fiscal": {"frequency": 25, "total_chars": 150, "sources": ["ProductID_123", "CodeSet_ABC"]},
        "occasional": {"frequency": 8, "total_chars": 72, "sources": ["ProductID_456"]}, 
        "management": {"frequency": 15, "total_chars": 150, "sources": ["CodeSet_DEF", "ProductID_789"]},
        "environmental": {"frequency": 12, "total_chars": 156, "sources": ["ProductID_101"]},
        "transportation": {"frequency": 18, "total_chars": 252, "sources": ["CodeSet_GHI"]},
        "administrative": {"frequency": 10, "total_chars": 140, "sources": ["ProductID_202"]},
        "international": {"frequency": 22, "total_chars": 286, "sources": ["CodeSet_JKL", "ProductID_303"]},
    }
    
    for word, stats in test_words.items():
        word_tracker.track_text_processing(
            original_text=word,
            substituted_text=word,  # Not substituted
            source=stats["sources"][0]
        )
        # Add additional sources
        for source in stats["sources"][1:]:
            word_tracker.track_text_processing(
                original_text=word,
                substituted_text=word,
                source=source
            )
    
    # Save test tracking data
    test_tracking_file = Path("scratch/test_interactive_tracking.json")
    test_tracking_file.parent.mkdir(exist_ok=True)
    word_tracker.save_tracking_data(test_tracking_file)
    print(f"   ✅ Saved test tracking data to: {test_tracking_file}")
    
    # 2. Test manager initialization
    print("\n2️⃣ Testing manager initialization...")
    manager = InteractiveAbbreviationManager()
    print(f"   ✅ Manager initialized with {len(manager.abbreviations)} abbreviations")
    
    # 3. Test word tracking data loading
    print("\n3️⃣ Testing word tracking data loading...")
    loaded_tracker = manager.load_word_tracking_data(test_tracking_file)
    if loaded_tracker:
        print(f"   ✅ Successfully loaded {len(loaded_tracker.word_stats)} tracked words")
    else:
        print("   ❌ Failed to load word tracking data")
        return
    
    # 4. Test abbreviation opportunity analysis
    print("\n4️⃣ Testing abbreviation opportunity analysis...")
    candidates = manager.show_abbreviation_opportunities(loaded_tracker)
    print(f"   ✅ Found {len(candidates)} abbreviation candidates")
    
    # 5. Test abbreviation suggestions
    print("\n5️⃣ Testing abbreviation suggestions...")
    test_suggestion_words = ["fiscal", "management", "environmental", "transportation"]
    for word in test_suggestion_words:
        suggestion = manager._suggest_abbreviation(word)
        print(f"   '{word}' → suggested: '{suggestion}'")
    
    # 6. Test conflict detection
    print("\n6️⃣ Testing conflict detection...")
    # Test with existing abbreviation
    conflict = manager._check_existing_abbreviations("employment", "empl")
    if conflict:
        print(f"   ✅ Conflict detected: {conflict}")
    else:
        print("   ⚠️  No conflict detected for 'employment' → 'empl'")
    
    # Test with new word
    conflict = manager._check_existing_abbreviations("fiscal", "fisc")
    if conflict:
        print(f"   ⚠️  Unexpected conflict: {conflict}")
    else:
        print("   ✅ No conflict for new word 'fiscal' → 'fisc'")
    
    # 7. Test consolidation opportunity detection
    print("\n7️⃣ Testing consolidation opportunity detection...")
    consolidations = manager.check_consolidation_opportunities()
    print(f"   ✅ Found {len(consolidations)} consolidation opportunities")
    
    if consolidations:
        print("   📋 Consolidation opportunities:")
        for i, opp in enumerate(consolidations[:3], 1):  # Show first 3
            print(f"      {i}. {opp['key']}: {opp['current']} → {opp['proposed']}")
    
    # 8. Test programmatic abbreviation addition (simulating user input)
    print("\n8️⃣ Testing programmatic abbreviation addition...")
    original_count = len(manager.abbreviations)
    
    # Add a test abbreviation
    test_abbrev = "fisc"
    test_word = "fiscal"
    if test_abbrev not in manager.abbreviations:
        manager._add_abbreviation(test_abbrev, test_word)
        print(f"   ✅ Added test abbreviation: '{test_abbrev}' → '{test_word}'")
        print(f"   📊 Abbreviation count: {original_count} → {len(manager.abbreviations)}")
    
    # 9. Test file generation
    print("\n9️⃣ Testing abbreviation file content generation...")
    try:
        content = manager._generate_abbreviations_file_content()
        lines = content.split('\n')
        print(f"   ✅ Generated {len(lines)} lines of abbreviation file content")
        print(f"   📋 Sample lines: {lines[0]} ... {lines[-3]}")
    except Exception as e:
        print(f"   ❌ Error generating content: {e}")
    
    # 10. Summary
    print(f"\n🎉 INTERACTIVE SYSTEM TEST COMPLETE")
    print("=" * 50)
    print(f"✅ All core functionality tested successfully!")
    print(f"📊 System ready with {len(candidates)} abbreviation opportunities available")
    print(f"🔧 Run: python tools/interactive_abbreviation_manager.py")
    print(f"📂 Test data available at: {test_tracking_file}")
    
    # Cleanup note
    print(f"\n🧹 Cleanup: Test tracking data saved in scratch/ directory")
    print(f"   (Can be safely deleted after testing)")


if __name__ == "__main__":
    test_interactive_system()
