#!/usr/bin/env python3
"""
Main entry point for running WDS enum generation.
This runs both ProductID and CodeSet enum generators with our optimized performance.
"""

import asyncio
import sys
from pathlib import Path
import argparse
from tools.wds_productid_enum_gen import ProductIdEnumWriter
from tools.wds_code_enum_gen import CodeSetEnumWriter
from tools.word_tracker import get_word_tracker, reset_word_tracker
from statscan.util.log import configure_logging


def main():
    parser = argparse.ArgumentParser(
        description="Generate WDS enums with optimized performance and abbreviation analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate all enums
    python tools/wds_enum_gen.py
    
    # Generate with word tracking for abbreviation analysis
    python tools/wds_enum_gen.py --track-words
    
    # Generate ProductID enums only
    python tools/wds_enum_gen.py --type product
    
    # Generate specific codeset with tracking
    python tools/wds_enum_gen.py --type codeset --codeset frequency --track-words
    
Word Tracking:
    The --track-words flag enables analysis of non-substituted words during enum
    generation to identify potential abbreviation opportunities. This helps optimize
    the abbreviation system by finding high-frequency words that could benefit from
    shorter abbreviations.
        """
    )
    parser.add_argument("--type", 
                        choices=["product", "codeset", "all"], 
                        default="all",
                        help="Type of enums to generate")
    parser.add_argument("--codeset", 
                        type=str,
                        help="Specific codeset to generate (e.g., 'uom', 'classification_type'). Use 'python tools/wds_code_enum_gen.py' to see available codesets. Only valid with --type codeset")
    parser.add_argument("--output-dir", 
                        type=Path,
                        default=Path("statscan/enums/auto/wds"),
                        help="Output directory for generated enums")
    parser.add_argument("--verbose", "-v", 
                        action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("--track-words", 
                        action="store_true",
                        help="Track non-substituted words for abbreviation analysis")
    parser.add_argument("--word-report", 
                        type=Path,
                        help="Generate word analysis report at specified path")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.codeset and args.type != "codeset":
        parser.error("--codeset can only be used with --type codeset")
    
    # Configure logging with standard format
    level = "DEBUG" if args.verbose else "INFO"
    configure_logging(level=level)
    
    async def run_generators():
        """Run the requested enum generators."""
        # Reset word tracker if tracking is enabled
        if args.track_words:
            reset_word_tracker()
            print("📝 Word tracking enabled - analyzing abbreviation opportunities...")
        
        if args.type in ("product", "all"):
            print("🏭 Generating ProductID Enums...")
            generator = ProductIdEnumWriter(track_words=args.track_words)
            product_file = args.output_dir / "product_id.py"
            await generator.fetch_and_create_enum(fp=product_file, overwrite=True, track_words=args.track_words)
            print(f"✅ ProductID enums generated: {product_file}")
        
        if args.type in ("codeset", "all"):
            print("\n📊 Generating CodeSet Enums...")
            generator = CodeSetEnumWriter(track_words=args.track_words)
            
            if args.codeset:
                # Generate specific codeset
                print(f"🎯 Targeting specific codeset: {args.codeset}")
                codeset_file = args.output_dir / f"{args.codeset}.py"
                result_file = await generator.fetch_and_create_single_enum(
                    codeset_name=args.codeset, 
                    fp=codeset_file, 
                    overwrite=True,
                    track_words=args.track_words
                )
                print(f"✅ CodeSet enum generated: {result_file}")
            else:
                # Generate all codesets
                codeset_files = await generator.fetch_and_create_enums(
                    output_dir=args.output_dir, 
                    overwrite=True,
                    track_words=args.track_words
                )
                print(f"✅ CodeSet enums generated: {len(codeset_files)} files in {args.output_dir}")
        
        # Generate word analysis report if tracking was enabled
        if args.track_words:
            word_tracker = get_word_tracker()
            if word_tracker.word_stats:
                print(f"\n📊 Tracked {len(word_tracker.word_stats)} unique words during generation")
                
                # Save tracking data
                tracking_file = Path("scratch/word_tracking_data.json")
                word_tracker.save_tracking_data(tracking_file)
                print(f"💾 Word tracking data saved: {tracking_file}")
                
                # Generate report
                report_file = args.word_report or Path("scratch/abbreviation_analysis_report.md")
                report = word_tracker.generate_abbreviation_report(
                    output_file=report_file,
                    include_contexts=True
                )
                
                print("\n" + "="*60)
                print("📋 ABBREVIATION OPPORTUNITY ANALYSIS")
                print("="*60)
                
                # Show summary of top candidates
                candidates = word_tracker.get_abbreviation_candidates()
                if candidates:
                    print(f"🎯 Found {len(candidates)} abbreviation candidates!")
                    print("\n🏆 TOP 10 CANDIDATES:")
                    for i, (word, stats) in enumerate(candidates[:10], 1):
                        print(f"  {i:2d}. '{word}' (frequency: {stats.frequency}, "
                              f"potential savings: {stats.total_potential_savings:.0f} chars)")
                    
                    print(f"\n📄 Full analysis saved to: {report_file}")
                    print("💡 Use this data to update tools/abbreviations.py with high-impact abbreviations")
                else:
                    print("✅ No significant abbreviation opportunities found - system is well optimized!")
            else:
                print("⚠️  No words tracked during generation")
    
    try:
        asyncio.run(run_generators())
        print(f"\n🎉 WDS enum generation complete! Files written to: {args.output_dir}")
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
