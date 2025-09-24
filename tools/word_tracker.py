#!/usr/bin/env python3
"""
Word Tracking System for Abbreviation Opportunity Analysis.

This module provides a comprehensive system for tracking non-substituted words
during WDS enum generation to identify potential abbreviation candidates.
"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union
import json
import logging
from datetime import datetime, timezone

from tools.substitution import SubstitutionEngine

logger = logging.getLogger(__name__)


@dataclass
class WordStats:
    """Statistics for a tracked word during enum generation."""
    word: str
    frequency: int = 0
    contexts: Set[str] = field(default_factory=set)
    sources: Set[str] = field(default_factory=set)  # Which generator/dataset
    max_length_impact: int = 0  # Maximum chars saved if abbreviated
    avg_length_impact: float = 0.0  # Average chars saved per occurrence
    
    def add_occurrence(self, context: str, source: str, potential_savings: int):
        """Add an occurrence of this word."""
        self.frequency += 1
        self.contexts.add(context)
        self.sources.add(source)
        self.max_length_impact = max(self.max_length_impact, potential_savings)
        
        # Update average length impact
        current_total = (self.avg_length_impact * (self.frequency - 1))
        self.avg_length_impact = (current_total + potential_savings) / self.frequency
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score for abbreviation consideration."""
        # Score based on: frequency × average_impact × word_length
        return self.frequency * self.avg_length_impact * len(self.word)
    
    @property
    def total_potential_savings(self) -> float:
        """Total character savings if this word was abbreviated."""
        # Estimate 3-4 character abbreviation on average
        avg_abbrev_length = min(4, len(self.word) // 2)
        savings_per_occurrence = max(0, len(self.word) - avg_abbrev_length)
        return self.frequency * savings_per_occurrence


class WordTracker:
    """
    Tracks and analyzes non-substituted words during enum generation.
    
    This class provides functionality to:
    1. Track words that don't get abbreviated
    2. Analyze frequency and impact patterns
    3. Generate prioritized abbreviation recommendations
    """
    
    def __init__(self, subs_engine: Optional[SubstitutionEngine] = None):
        self.subs_engine = subs_engine or SubstitutionEngine()
        self.word_stats: Dict[str, WordStats] = {}
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.min_word_length = 4  # Only track words >= 4 chars
        self.max_tracked_words = 10000  # Prevent memory overflow
        
    def track_text_processing(self, 
                            original_text: str, 
                            substituted_text: str, 
                            source: str = "unknown") -> Dict[str, int]:
        """
        Track the processing of text through substitution engine.
        
        Args:
            original_text: Original text before substitution
            substituted_text: Text after substitution
            source: Source identifier (e.g., "ProductID", "CodeSet:frequency")
            
        Returns:
            Dictionary of non-substituted words and their lengths
        """
        # Extract words from original text
        original_words = self._extract_words(original_text)
        substituted_words = self._extract_words(substituted_text)
        
        # Find words that weren't substituted or were poorly substituted
        non_substituted = {}
        
        for word in original_words:
            if len(word) < self.min_word_length:
                continue
                
            # Skip if already tracking too many words
            if (len(self.word_stats) >= self.max_tracked_words and 
                word not in self.word_stats):
                continue
            
            # Check if word appears unchanged in result
            word_lower = word.lower()
            if any(word_lower in sub_word.lower() for sub_word in substituted_words):
                # Word wasn't effectively substituted
                potential_savings = len(word) - 4  # Assume 4-char abbreviation
                if potential_savings > 0:
                    non_substituted[word] = potential_savings
                    
                    # Update word stats
                    if word_lower not in self.word_stats:
                        self.word_stats[word_lower] = WordStats(word=word_lower)
                    
                    self.word_stats[word_lower].add_occurrence(
                        context=original_text[:100],  # First 100 chars as context
                        source=source,
                        potential_savings=potential_savings
                    )
        
        return non_substituted
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text."""
        # Remove common delimiters and extract alphabetic sequences
        words = re.findall(r'[A-Za-z]{3,}', text)
        
        # Filter out very common/stop words that aren't useful for abbreviation
        stop_words = {
            'the', 'and', 'for', 'are', 'not', 'but', 'had', 'has', 'was', 
            'his', 'her', 'you', 'all', 'can', 'may', 'get', 'got', 'put',
            'use', 'new', 'old', 'see', 'way', 'who', 'boy', 'did', 'its',
            'let', 'say', 'she', 'too', 'any', 'day', 'man', 'now', 'our',
            'out', 'two', 'how', 'end', 'why', 'own', 'run', 'off', 'try'
        }
        
        return [word for word in words if word.lower() not in stop_words]
    
    def get_abbreviation_candidates(self, 
                                  min_frequency: int = 3,
                                  min_length: int = 6,
                                  max_results: int = 50) -> List[Tuple[str, WordStats]]:
        """
        Get prioritized list of abbreviation candidates.
        
        Args:
            min_frequency: Minimum frequency to be considered
            min_length: Minimum word length to be considered  
            max_results: Maximum number of results to return
            
        Returns:
            List of (word, stats) tuples sorted by priority score
        """
        candidates = []
        
        for word, stats in self.word_stats.items():
            if (stats.frequency >= min_frequency and 
                len(word) >= min_length):
                candidates.append((word, stats))
        
        # Sort by priority score (frequency × impact × length)
        candidates.sort(key=lambda x: x[1].priority_score, reverse=True)
        
        return candidates[:max_results]
    
    def generate_abbreviation_report(self, 
                                   output_file: Optional[Path] = None,
                                   include_contexts: bool = False,
                                   format_markdown: bool = True) -> str:
        """
        Generate a comprehensive abbreviation opportunity report.
        
        Args:
            output_file: Optional file to write report to
            include_contexts: Whether to include usage contexts
            format_markdown: Whether to generate markdown format (default: True)
            
        Returns:
            Report string
        """
        candidates = self.get_abbreviation_candidates()
        
        if format_markdown:
            report_lines = [
                "# 🔍 Abbreviation Opportunity Analysis Report",
                "",
                f"**📊 Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
                f"**📈 Session:** `{self.session_id}`  ",
                f"**📝 Total unique words tracked:** {len(self.word_stats)}  ",
                f"**🎯 High-priority candidates:** {len(candidates)}  ",
                "",
                "---",
                ""
            ]
        else:
            report_lines = [
                "🔍 Abbreviation Opportunity Analysis Report",
                f"📊 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"📈 Session: {self.session_id}",
                f"📝 Total unique words tracked: {len(self.word_stats)}",
                f"🎯 High-priority candidates: {len(candidates)}",
                "=" * 80,
                ""
            ]
        
        if not candidates:
            if format_markdown:
                report_lines.extend([
                    "## 🎉 No Significant Abbreviation Opportunities Found!",
                    "",
                    "The current abbreviation system appears well-optimized.",
                    ""
                ])
            else:
                report_lines.extend([
                    "🎉 No significant abbreviation opportunities found!",
                    "The current abbreviation system appears well-optimized.",
                    ""
                ])
        else:
            if format_markdown:
                report_lines.extend([
                    "## 🏆 Top Abbreviation Candidates",
                    "",
                    "| Rank | Word | Freq | Avg Save | Total Save | Priority Score | Sources |",
                    "|------|------|------|----------|------------|----------------|---------|"
                ])
                
                for i, (word, stats) in enumerate(candidates[:25], 1):
                    sources_str = ", ".join(sorted(stats.sources))[:30]
                    if len(", ".join(stats.sources)) > 30:
                        sources_str += "..."
                    
                    report_lines.append(
                        f"| {i} | `{word}` | {stats.frequency} | "
                        f"{stats.avg_length_impact:.1f} | {stats.total_potential_savings:.0f} | "
                        f"{stats.priority_score:.0f} | {sources_str} |"
                    )
                
                report_lines.extend(["", ""])
            else:
                report_lines.extend([
                    "🏆 TOP ABBREVIATION CANDIDATES",
                    f"{'Rank':<4} {'Word':<20} {'Freq':<6} {'AvgSave':<8} {'TotalSave':<10} {'Score':<8} Sources",
                    "-" * 80
                ])
                
                for i, (word, stats) in enumerate(candidates[:25], 1):
                    sources_str = ", ".join(sorted(stats.sources))[:30] + ("..." if len(", ".join(stats.sources)) > 30 else "")
                    
                    report_lines.append(
                        f"{i:<4} {word:<20} {stats.frequency:<6} "
                        f"{stats.avg_length_impact:<8.1f} {stats.total_potential_savings:<10.0f} "
                        f"{stats.priority_score:<8.0f} {sources_str}"
                    )
            
            if len(candidates) > 25:
                report_lines.append(f"... and {len(candidates) - 25} more candidates")
        
        if format_markdown:
            report_lines.extend(["---", "", "## 📋 Recommendations", ""])
        else:
            report_lines.extend(["", "📋 RECOMMENDATIONS", "=" * 80])
        
        if candidates:
            # Group by common patterns
            length_groups = defaultdict(list)
            source_groups = defaultdict(list)
            
            for word, stats in candidates[:10]:
                length_groups[len(word)].append((word, stats))
                for source in stats.sources:
                    source_groups[source].append((word, stats))
            
            if format_markdown:
                report_lines.extend([
                    "### 🎯 Priority Actions:",
                    "",
                    "1. Consider abbreviating top 5-10 words for immediate impact",
                    "2. Focus on words with frequency ≥ 5 and length ≥ 8 characters", 
                    "3. Target sources with highest word concentration",
                    ""
                ])
            else:
                report_lines.extend([
                    "",
                    "🎯 **Priority Actions:**",
                    f"1. Consider abbreviating top 5-10 words for immediate impact",
                    f"2. Focus on words with frequency ≥ 5 and length ≥ 8 characters",
                    f"3. Target sources with highest word concentration",
                    ""
                ])
            
            # Source analysis
            if source_groups:
                if format_markdown:
                    report_lines.extend([
                        "### 📊 Impact by Source:",
                        ""
                    ])
                    for source in sorted(source_groups.keys()):
                        words = source_groups[source]
                        total_savings = sum(stats.total_potential_savings for _, stats in words)
                        report_lines.append(f"- **{source}**: {len(words)} words, ~{total_savings:.0f} char savings")
                else:
                    report_lines.extend([
                        "📊 **Impact by Source:**"
                    ])
                    for source in sorted(source_groups.keys()):
                        words = source_groups[source]
                        total_savings = sum(stats.total_potential_savings for _, stats in words)
                        report_lines.append(f"   • {source}: {len(words)} words, ~{total_savings:.0f} char savings")
            
            # Suggested abbreviations for top candidates
            report_lines.extend([
                "",
                "💡 **Suggested Abbreviations for Top 10:**"
            ])
            
            for word, stats in candidates[:10]:
                suggested_abbrev = self._suggest_abbreviation(word)
                savings = len(word) - len(suggested_abbrev)
                total_impact = savings * stats.frequency
                report_lines.append(
                    f"   • '{word}' → '{suggested_abbrev}' "
                    f"(saves {savings} chars × {stats.frequency} uses = {total_impact} total)"
                )
        
        else:
            report_lines.extend([
                "✅ The abbreviation system appears well-optimized",
                "🔄 Continue monitoring during future enum generations",
                "📈 Consider lowering thresholds if more candidates needed"
            ])
        
        # Add contexts if requested
        if include_contexts and candidates:
            report_lines.extend([
                "",
                "🔍 USAGE CONTEXTS (Top 5 words)",
                "=" * 80
            ])
            
            for word, stats in candidates[:5]:
                report_lines.extend([
                    f"",
                    f"📝 Word: '{word}' (frequency: {stats.frequency})",
                    f"   Sources: {', '.join(sorted(stats.sources))}",
                    f"   Sample contexts:"
                ])
                
                for i, context in enumerate(sorted(stats.contexts)[:3], 1):
                    report_lines.append(f"   {i}. {context}...")
        
        report = "\n".join(report_lines)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report, encoding='utf-8')
            logger.info(f"📄 Report written to: {output_file}")
        
        return report
    
    def _suggest_abbreviation(self, word: str) -> str:
        """Suggest a reasonable abbreviation for a word."""
        word = word.lower()
        
        # Common abbreviation patterns
        if len(word) <= 4:
            return word[:3]
        elif len(word) <= 6:
            return word[:4]
        elif word.endswith('tion'):
            return word[:4]  # education -> educ
        elif word.endswith('ing'):
            return word[:-3][:4]  # building -> buil
        elif word.endswith('ment'):
            return word[:4]  # management -> mgmt (special case) or mana
        elif word.endswith('ness'):
            return word[:-4][:4]  # business -> busi
        else:
            # Try to keep consonants and remove vowels intelligently
            consonants = re.sub(r'[aeiou]', '', word[1:])  # Keep first char
            if len(consonants) >= 3:
                return (word[0] + consonants[:3]).ljust(4, word[-1])
            else:
                return word[:4]
    
    def save_tracking_data(self, output_file: Path):
        """Save tracking data to JSON file for further analysis."""
        word_stats_dict: dict[str, dict] = {}
        
        for word, stats in self.word_stats.items():
            word_stats_dict[word] = {
                'frequency': stats.frequency,
                'contexts': list(stats.contexts)[:10],  # Limit contexts to save space
                'sources': list(stats.sources),
                'max_length_impact': stats.max_length_impact,
                'avg_length_impact': stats.avg_length_impact,
                'priority_score': stats.priority_score,
                'total_potential_savings': stats.total_potential_savings
            }
        
        data = {
            'session_id': self.session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_words': len(self.word_stats),
            'word_stats': word_stats_dict
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 Tracking data saved to: {output_file}")
    
    def load_tracking_data(self, input_file: Path):
        """Load previously saved tracking data."""
        if not input_file.exists():
            logger.warning(f"📁 Tracking file not found: {input_file}")
            return
        
        with input_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.session_id = data.get('session_id', self.session_id)
        
        for word, stats_data in data.get('word_stats', {}).items():
            stats = WordStats(
                word=word,
                frequency=stats_data['frequency'],
                contexts=set(stats_data['contexts']),
                sources=set(stats_data['sources']),
                max_length_impact=stats_data['max_length_impact'],
                avg_length_impact=stats_data['avg_length_impact']
            )
            self.word_stats[word] = stats
        
        logger.info(f"📁 Loaded {len(self.word_stats)} word stats from: {input_file}")


# Global instance for easy access
_global_word_tracker: Optional[WordTracker] = None


def get_word_tracker():
    """Get the global word tracker instance."""
    global _global_word_tracker
    if _global_word_tracker is None:
        _global_word_tracker = WordTracker()
    return _global_word_tracker


def reset_word_tracker():
    """Reset the global word tracker."""
    global _global_word_tracker
    _global_word_tracker = None


if __name__ == "__main__":
    import argparse
    from statscan.util.log import configure_logging
    
    parser = argparse.ArgumentParser(
        description="Analyze tracked word data for abbreviation opportunities"
    )
    parser.add_argument('--input', type=Path,
                       help='Input JSON file with tracking data')
    parser.add_argument('--output', type=Path, 
                       default=Path('scratch/abbreviation_analysis_report.md'),
                       help='Output file for analysis report')
    parser.add_argument('--min-frequency', type=int, default=3,
                       help='Minimum frequency for candidates')
    parser.add_argument('--min-length', type=int, default=6,
                       help='Minimum word length for candidates')
    parser.add_argument('--max-results', type=int, default=50,
                       help='Maximum number of candidates to show')
    parser.add_argument('--include-contexts', action='store_true',
                       help='Include usage contexts in report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    configure_logging(level="DEBUG" if args.verbose else "INFO")
    
    tracker = WordTracker()
    
    if args.input:
        tracker.load_tracking_data(args.input)
        
        if not tracker.word_stats:
            print("❌ No word stats loaded. Run enum generation with word tracking first.")
            exit(1)
        
        print(f"📊 Loaded {len(tracker.word_stats)} tracked words")
        print("🔍 Generating abbreviation analysis report...")
        
        report = tracker.generate_abbreviation_report(
            output_file=args.output,
            include_contexts=args.include_contexts
        )
        
        print(report)
        print(f"\n📄 Full report saved to: {args.output}")
        
    else:
        print("📋 Word Tracker Analysis Tool")
        print("Usage: First run enum generation with word tracking enabled,")
        print("       then use --input to analyze the collected data.")
        print("\nExample:")
        print("  python tools/wds_enum_gen.py --track-words")
        print("  python tools/word_tracker.py --input scratch/word_tracking_data.json")
