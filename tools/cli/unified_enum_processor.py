#!/usr/bin/env python3
"""Unified Enum Processing System

This module provides a unified interface for processing multiple enum generators
with optional word tracking and abbreviation analysis.
"""

import argparse
import asyncio
import logging
from pathlib import Path
from typing import cast

from statscan.util.log import configure_logging
from tools.cli.wds_code_enum_gen import CodeSetEnumWriter
from tools.cli.wds_productid_enum_gen import ProductIdEnumWriter
from tools.word_tracker import WordTracker, get_word_tracker, reset_word_tracker

logger = logging.getLogger(__name__)


class UnifiedEnumProcessor:
    """Unified processor for handling multiple enum generators with consistent interface

    This class provides a single entry point for processing all enum types with
    optional word tracking and analysis capabilities.
    """

    def __init__(self, track_words: bool = False):
        """Initialize the unified processor.

        Args:
            track_words: If True, enable word tracking across all generators

        """
        self.track_words = track_words

        # Initialize generators with word tracking
        self.product_generator = ProductIdEnumWriter(track_words=track_words)
        self.codeset_generator = CodeSetEnumWriter(track_words=track_words)

        # Reset word tracker if tracking is enabled
        if track_words:
            reset_word_tracker()

    async def process_all(
        self,
        output_dir: Path,
        overwrite: bool = False,
        include_types: list[str] | None = None,
    ) -> dict[str, Path | dict[str, Path]]:
        """Process all enum types.

        Args:
            output_dir: Base output directory
            overwrite: Whether to overwrite existing files
            include_types: List of types to include (e.g. "product", "codeset"),
                           or None for all

        Returns:
            Dictionary mapping generator types to their output results

        """
        if include_types is None:
            include_types = ["product", "codeset"]

        results: dict[str, Path | dict[str, Path]] = {}

        logger.info(
            f"🔄 Starting unified enum processing for: {', '.join(include_types)}"
        )

        if "product" in include_types:
            logger.info("🏭 Processing ProductID enums...")
            product_file = output_dir / "product_id.py"
            results["product"] = await self.product_generator.process(
                fp=product_file, overwrite=overwrite
            )
            logger.info(f"✅ ProductID processing complete: {results['product']}")

        if "codeset" in include_types:
            logger.info("📊 Processing CodeSet enums...")
            codeset_dir = output_dir / "codesets"
            codeset_result = await self.codeset_generator.process(
                output_dir=codeset_dir, overwrite=overwrite
            )
            results["codeset"] = cast(Path | dict[str, Path], codeset_result)
            if isinstance(results["codeset"], dict):
                logger.info(
                    f"✅ CodeSet processing complete: {len(results['codeset'])} files"
                )
            else:
                logger.info(f"✅ CodeSet processing complete: {results['codeset']}")

        return results

    async def process_specific_codeset(
        self, codeset_name: str, output_file: Path, overwrite: bool = False
    ) -> Path:
        """Process a specific codeset only.

        Args:
            codeset_name: Name of the specific codeset
            output_file: Output file path
            overwrite: Whether to overwrite existing files

        Returns:
            Path to the generated file

        """
        logger.info(f"🎯 Processing specific codeset: {codeset_name}")

        result = await self.codeset_generator.process_single(
            codeset_name=codeset_name, fp=output_file, overwrite=overwrite
        )

        logger.info(f"✅ Specific codeset processing complete: {result}")
        return result

    def get_word_analysis(self) -> WordTracker | None:
        """Get word tracker for analysis if word tracking is enabled.

        Returns:
            WordTracker instance or None if tracking is disabled

        """
        return get_word_tracker() if self.track_words else None

    def generate_word_analysis_report(
        self, output_file: Path | None = None, include_contexts: bool = True
    ) -> str | None:
        """Generate word analysis report if tracking is enabled.

        Args:
            output_file: Optional file to write report to
            include_contexts: Whether to include usage contexts

        Returns:
            Report string or None if tracking is disabled

        """
        if not self.track_words:
            logger.warning("Word tracking is not enabled - no report generated")
            return None

        word_tracker = get_word_tracker()
        if not word_tracker.word_stats:
            logger.warning("No word data collected - no report generated")
            return None

        logger.info("📊 Generating word analysis report...")

        if output_file is None:
            output_file = Path("scratch/unified_abbreviation_analysis.md")

        # Generate abbreviation analysis report
        report = word_tracker.generate_abbreviation_report(
            output_file=output_file, include_contexts=include_contexts
        )

        logger.info(f"📄 Word analysis report generated: {output_file}")
        return report

    def save_word_tracking_data(
        self, output_file: Path | None = None
    ) -> Path | None:
        """Save word tracking data if tracking is enabled.

        Args:
            output_file: Optional file to save data to

        Returns:
            Path to saved file or None if tracking is disabled

        """
        if not self.track_words:
            logger.warning("Word tracking is not enabled - no data to save")
            return None

        word_tracker = get_word_tracker()
        if not word_tracker.word_stats:
            logger.warning("No word data collected - nothing to save")
            return None

        if output_file is None:
            output_file = Path("scratch/unified_word_tracking_data.json")

        word_tracker.save_tracking_data(output_file)
        logger.info(f"💾 Word tracking data saved: {output_file}")
        return output_file

    def print_word_analysis_summary(self) -> None:
        """Print a summary of word analysis if tracking is enabled."""
        if not self.track_words:
            print("⚠️  Word tracking is not enabled")
            return

        word_tracker = get_word_tracker()
        if not word_tracker.word_stats:
            print("⚠️  No word data collected during processing")
            return

        candidates = word_tracker.get_abbreviation_candidates(
            min_frequency=2, min_length=5, max_results=10
        )

        print("\n📊 Word Analysis Summary")
        print("=" * 50)
        print(f"📈 Total unique words tracked: {len(word_tracker.word_stats)}")
        print(f"🎯 Abbreviation candidates found: {len(candidates)}")

        if candidates:
            total_savings = sum(
                stats.total_potential_savings for _, stats in candidates
            )
            print(f"💰 Total potential character savings: {total_savings:.0f}")

            print("\n🏆 Top 5 Abbreviation Opportunities:")
            for i, (word, stats) in enumerate(candidates[:5], 1):
                print(
                    f"  {i}. '{word}' → freq:{stats.frequency}, \
                        savings:{stats.total_potential_savings:.0f}"
                )
        else:
            print(
                "✅ No significant abbreviation opportunities found - system is well \
                    optimized!"
            )


async def main():
    """Example usage of the unified processor."""
    parser = argparse.ArgumentParser(
        description="Unified enum processing with optional word tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process all enums with word tracking
    python tools/unified_enum_processor.py --track-words

    # Process only ProductID enums
    python tools/unified_enum_processor.py --types product

    # Process specific codeset with tracking
    python tools/unified_enum_processor.py --types codeset --codeset frequency --track-words
        """,  # noqa: E501
    )

    parser.add_argument(
        "--types",
        nargs="+",
        choices=["product", "codeset"],
        default=["product", "codeset"],
        help="Types of enums to process (default: all)",
    )
    parser.add_argument(
        "--codeset",
        type=str,
        help="Specific codeset to process (requires --types codeset)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scratch/unified_enums"),
        help="Output directory (default: scratch/unified_enums)",
    )
    parser.add_argument(
        "--track-words",
        action="store_true",
        help="Enable word tracking for abbreviation analysis",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Configure logging
    configure_logging(level="DEBUG" if args.verbose else "INFO")

    # Validate arguments
    if args.codeset and "codeset" not in args.types:
        parser.error("--codeset can only be used when 'codeset' is in --types")

    try:
        # Initialize processor
        processor = UnifiedEnumProcessor(track_words=args.track_words)

        # Process enums
        if args.codeset:
            # Process specific codeset
            output_file = args.output_dir / f"{args.codeset}.py"
            result = await processor.process_specific_codeset(
                codeset_name=args.codeset,
                output_file=output_file,
                overwrite=args.overwrite,
            )
            print(f"✅ Processed codeset '{args.codeset}': {result}")
        else:
            # Process requested types
            results = await processor.process_all(
                output_dir=args.output_dir,
                overwrite=args.overwrite,
                include_types=args.types,
            )

            # Print results summary
            print("\n✅ Processing complete!")
            for enum_type, result in results.items():
                if isinstance(result, dict):
                    print(f"  📊 {enum_type}: {len(result)} files generated")
                else:
                    print(f"  🏭 {enum_type}: {result}")

        # Generate word analysis if tracking was enabled
        if args.track_words:
            processor.print_word_analysis_summary()

            # Save detailed analysis
            analysis_dir = args.output_dir / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)

            processor.save_word_tracking_data(analysis_dir / "word_tracking_data.json")
            processor.generate_word_analysis_report(
                analysis_dir / "abbreviation_analysis_report.md"
            )

            print(f"\n📁 Analysis files saved in: {analysis_dir}")

    except Exception as e:
        logger.error(f"❌ Processing failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
