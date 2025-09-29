#!/usr/bin/env python3
"""
Enhanced Interactive Abbreviation Management System

This script provides comprehensive abbreviation management with:
1. Morphological conflict resolution
2. Consolidation opportunities implementation
3. New abbreviation addition from discovered opportunities
4. Quality validation and testing
"""

from pathlib import Path
import re
from typing import Optional
from tools.abbreviations import DEFAULT_ABBREVIATIONS
from tools.word_tracker import WordTracker
from tools.substitution import SubstitutionEngine

class InteractiveAbbreviationManager:
    """
    Interactive manager for abbreviation dictionary maintenance and enhancement.
    """

    def __init__(self):
        self.abbreviations = dict(DEFAULT_ABBREVIATIONS)
        self.changes_made = []
        self.subs_engine = SubstitutionEngine()

    def load_word_tracking_data(self, tracking_file: Path) -> Optional[WordTracker]:
        """Load word tracking data from file."""
        if not tracking_file.exists():
            print(f"📂 Word tracking file not found: {tracking_file}")
            return None

        try:
            word_tracker = WordTracker()
            word_tracker.load_tracking_data(tracking_file)

            if word_tracker.word_stats:
                print(
                    f"📊 Loaded {len(word_tracker.word_stats)} tracked words from: {tracking_file}"
                )
                return word_tracker
            else:
                print(f"⚠️  No word stats found in tracking file: {tracking_file}")
                return None
        except Exception as e:
            print(f"❌ Error loading word tracking data: {e}")
            return None

    def show_abbreviation_opportunities(
        self, word_tracker: WordTracker, max_candidates: int = 20
    ):
        """Show abbreviation opportunities from word tracking data."""
        candidates = word_tracker.get_abbreviation_candidates(
            min_frequency=2, min_length=5, max_results=max_candidates
        )

        if not candidates:
            print(
                "✅ No significant abbreviation opportunities found in tracking data!"
            )
            return []

        print(
            f"\n🎯 ABBREVIATION OPPORTUNITIES FROM WORD TRACKING ({len(candidates)} found)"
        )
        print("=" * 80)
        print(
            f"{'#':<3} {'Word':<20} {'Freq':<6} {'Savings':<8} {'Suggested':<12} {'Sources'}"
        )
        print("-" * 80)

        for i, (word, stats) in enumerate(candidates, 1):
            suggested = self._suggest_abbreviation(word)
            sources_str = ", ".join(sorted(stats.sources))[:20]
            if len(", ".join(stats.sources)) > 20:
                sources_str += "..."

            print(
                f"{i:<3} {word:<20} {stats.frequency:<6} {stats.total_potential_savings:<8.0f} "
                f"{suggested:<12} {sources_str}"
            )

        return candidates

    def interactive_add_abbreviations(self, candidates: list):
        """Interactively add new abbreviations from candidates."""
        print("\n💡 INTERACTIVE ABBREVIATION ADDITION")
        print("=" * 60)
        print("📝 You can add new abbreviations based on the discovered opportunities.")
        print("🔍 For each suggestion, you can:")
        print("   1. Accept the suggested abbreviation")
        print("   2. Enter a custom abbreviation")
        print("   3. Skip this word")
        print("   4. Quit abbreviation addition")
        print()

        added_count = 0

        for i, (word, stats) in enumerate(candidates, 1):
            print(f"\n📝 Candidate #{i}: '{word}'")
            print(f"   📊 Frequency: {stats.frequency} occurrences")
            print(
                f"   💰 Potential savings: {stats.total_potential_savings:.0f} characters"
            )
            print(f"   📍 Sources: {', '.join(sorted(stats.sources))}")

            suggested = self._suggest_abbreviation(word)
            print(f"   💡 Suggested abbreviation: '{suggested}'")

            # Check if word or similar already exists
            existing_conflict = self._check_existing_abbreviations(word, suggested)
            if existing_conflict:
                print(f"   ⚠️  Potential conflict: {existing_conflict}")

            # Test morphological coverage if available
            if self.subs_engine:
                try:
                    variants = self.subs_engine._generate_variants_static(suggested)
                    if word.lower() in {v.lower() for v in variants}:
                        print(
                            f"   ✅ Morphological coverage confirmed: '{suggested}' → {word}"
                        )
                    else:
                        print(
                            f"   ❌ Morphological coverage issue: '{suggested}' doesn't generate '{word}'"
                        )
                        print(f"      Generated variants: {sorted(variants)[:5]}...")
                except Exception as e:
                    print(f"   ❌ Error testing morphological coverage: {e}")

            while True:
                choice = (
                    input(
                        f"\n   Choose action [1=Accept '{suggested}', 2=Custom, 3=Skip, 4=Quit, ?=Help]: "
                    )
                    .strip()
                    .lower()
                )

                if choice == "?":
                    print("   📋 Help:")
                    print("     1 - Accept the suggested abbreviation")
                    print("     2 - Enter a custom abbreviation")
                    print("     3 - Skip this word (don't add abbreviation)")
                    print("     4 - Quit and save current changes")
                    continue
                elif choice in ["1", "accept", "y", "yes"]:
                    # Accept suggested abbreviation
                    self._add_abbreviation(suggested, word)
                    added_count += 1
                    print(f"   ✅ Added: '{suggested}' → ['{word}']")
                    break
                elif choice in ["2", "custom", "c"]:
                    # Custom abbreviation
                    while True:
                        custom = input("   Enter custom abbreviation: ").strip().lower()
                        if not custom:
                            print("   ❌ Abbreviation cannot be empty")
                            continue
                        if not re.match(r"^[a-z][a-z0-9_]*$", custom):
                            print(
                                "   ❌ Abbreviation must start with letter and contain only lowercase letters, numbers, and underscores"
                            )
                            continue
                        if custom in self.abbreviations:
                            print(
                                f"   ⚠️  Abbreviation '{custom}' already exists with values: {self.abbreviations[custom]}"
                            )
                            confirm = (
                                input("   Add to existing entry? [y/n]: ")
                                .strip()
                                .lower()
                            )
                            if confirm in ["y", "yes"]:
                                self._add_abbreviation(custom, word)
                                added_count += 1
                                print(
                                    f"   ✅ Added to existing: '{custom}' → {self.abbreviations[custom]}"
                                )
                                break
                        else:
                            # Test morphological coverage for custom abbreviation
                            if self.subs_engine:
                                try:
                                    variants = (
                                        self.subs_engine._generate_variants_static(
                                            custom
                                        )
                                    )
                                    if word.lower() in {v.lower() for v in variants}:
                                        print(
                                            f"   ✅ Custom abbreviation works: '{custom}' → {word}"
                                        )
                                    else:
                                        print(
                                            f"   ⚠️  Custom abbreviation may not cover '{word}'"
                                        )
                                        print(
                                            f"      Generated variants: {sorted(variants)[:5]}..."
                                        )
                                        confirm = (
                                            input("   Use anyway? [y/n]: ")
                                            .strip()
                                            .lower()
                                        )
                                        if confirm not in ["y", "yes"]:
                                            continue
                                except Exception as e:
                                    print(
                                        f"   ❌ Error testing custom abbreviation: {e}"
                                    )

                            self._add_abbreviation(custom, word)
                            added_count += 1
                            print(f"   ✅ Added custom: '{custom}' → ['{word}']")
                            break
                    break
                elif choice in ["3", "skip", "s", "n", "no"]:
                    print(f"   ⏭️  Skipped '{word}'")
                    break
                elif choice in ["4", "quit", "q"]:
                    print(
                        f"   🛑 Quitting abbreviation addition (added {added_count} so far)"
                    )
                    return added_count
                else:
                    print(
                        "   ❌ Invalid choice. Please enter 1, 2, 3, 4, or ? for help."
                    )

        print(
            f"\n✅ Abbreviation addition complete! Added {added_count} new abbreviations."
        )
        return added_count

    def _suggest_abbreviation(self, word: str) -> str:
        """Generate a smart abbreviation suggestion for a word."""
        word_lower = word.lower()

        # Common abbreviation patterns
        if len(word) <= 4:
            return word_lower
        elif word_lower.endswith("tion"):
            return word_lower[:4]
        elif word_lower.endswith("ing"):
            base = word_lower[:-3]
            return base[:4] if len(base) > 4 else base
        elif word_lower.endswith("ment"):
            if word_lower == "management":
                return "mgmt"
            elif word_lower == "development":
                return "dev"
            elif word_lower == "environment":
                return "env"
            else:
                return word_lower[:4]
        elif word_lower.endswith("ness"):
            return word_lower[:-4][:4]
        elif word_lower in ["administration", "administrative"]:
            return "admin"
        elif word_lower in ["information", "informational"]:
            return "info"
        elif word_lower in ["international"]:
            return "intl"
        elif word_lower in ["government", "governmental"]:
            return "govt"
        elif word_lower in ["transportation", "transport"]:
            return "trans"
        elif word_lower in ["education", "educational"]:
            return "edu"
        elif word_lower in ["technology", "technological"]:
            return "tech"
        elif word_lower in ["organization", "organizational"]:
            return "org"
        elif word_lower in ["professional"]:
            return "prof"
        elif word_lower in ["construction"]:
            return "const"
        else:
            # Remove vowels intelligently, keep consonants
            consonants = "".join(c for c in word_lower[1:] if c not in "aeiou")
            if len(consonants) >= 3:
                return word_lower[0] + consonants[:3]
            else:
                return word_lower[:4]

    def _check_existing_abbreviations(self, word: str, suggested: str) -> Optional[str]:
        """Check for existing abbreviation conflicts."""
        word_lower = word.lower()

        # Check if word already exists in any abbreviation list
        for key, values in self.abbreviations.items():
            if word_lower in [v.lower() for v in values]:
                return f"Word '{word}' already abbreviated by '{key}'"

        # Check if suggested abbreviation already exists
        if suggested in self.abbreviations:
            return f"Abbreviation '{suggested}' already exists: {self.abbreviations[suggested]}"

        return None

    def _add_abbreviation(self, abbrev_key: str, word: str):
        """Add a word to an abbreviation key."""
        if abbrev_key in self.abbreviations:
            if word not in self.abbreviations[abbrev_key]:
                self.abbreviations[abbrev_key].append(word)
        else:
            self.abbreviations[abbrev_key] = [word]

        self.changes_made.append(f"Added '{word}' to abbreviation '{abbrev_key}'")

    def check_consolidation_opportunities(self):
        """Check for consolidation opportunities where morphological variants can reduce explicit entries."""
        opportunities = []
        for key, values in self.abbreviations.items():
            if len(values) > 1:  # Only check entries with multiple values
                try:
                    # Test if the abbreviation key itself could generate all the required terms
                    key_variants = self.subs_engine._generate_variants_static(key)
                    key_variants_lower = {v.lower() for v in key_variants}
                    values_lower = {v.lower() for v in values}

                    # Check if all explicit values are covered by the key's variants
                    covered_values = values_lower.intersection(key_variants_lower)
                    if len(covered_values) == len(values_lower):
                        # Check if this consolidation would conflict with other entries
                        conflicts = []
                        for other_key, other_values in self.abbreviations.items():
                            if other_key != key:
                                other_values_lower = {v.lower() for v in other_values}
                                overlap = key_variants_lower.intersection(
                                    other_values_lower
                                )
                                if overlap:
                                    conflicts.append(f"'{other_key}': {list(overlap)}")

                        if not conflicts:
                            opportunities.append(
                                {
                                    "type": "CONSOLIDATION",
                                    "key": key,
                                    "current": values,
                                    "proposed": [key],
                                    "covered_terms": sorted(covered_values),
                                    "description": f"Morphological variants of '{key}' cover all explicit terms",
                                }
                            )

                except Exception:
                    # Skip analysis for this key if it fails
                    continue

        return opportunities

    def interactive_consolidation_implementation(self):
        """Interactively implement consolidation opportunities."""
        print("\n🎯 MORPHOLOGICAL CONSOLIDATION OPPORTUNITIES")
        print("=" * 60)
        print("💡 Legend: **KEY** = dictionary key being modified")
        print("           🧬 = morphological variants generated automatically")
        print("           ✨ = optimization opportunity")
        print()

        opportunities = self.check_consolidation_opportunities()

        if not opportunities:
            print(
                "✅ No consolidation opportunities found - abbreviations are already optimized!"
            )
            return 0

        print(f"🔍 Found {len(opportunities)} consolidation opportunities:")

        applied_count = 0

        for i, opp in enumerate(opportunities, 1):
            print(f"\n✨ Opportunity #{i}: {opp['type']}")
            print(f"📋 **{opp['key']}**: Current substitution list")

            # Show current values with clear formatting
            current_values_str = ", ".join(f'"{v}"' for v in opp["current"])
            print(f"   Current: [{current_values_str}]")

            proposed_values_str = ", ".join(f'"{v}"' for v in opp["proposed"])
            print(f"   Proposed: [{proposed_values_str}]")
            print(f"   💡 {opp['description']}")

            # Show morphological coverage
            try:
                variants = self.subs_engine._generate_variants_static(opp["key"])
                print(
                    f"   🧬 **{opp['key']}** morphological variants: {sorted(variants)[:10]}..."
                )
                print(f"   ✅ Coverage confirmed: {opp['covered_terms']}")
            except Exception as e:
                print(f"   ❌ Error testing morphological coverage: {e}")
                continue

            while True:
                choice = input("\n   Apply consolidation? [y/n/q]: ").strip().lower()

                if choice in ["y", "yes", "1"]:
                    # Apply consolidation
                    old_values = self.abbreviations[opp["key"]].copy()
                    self.abbreviations[opp["key"]] = opp["proposed"].copy()
                    self.changes_made.append(
                        f"Consolidated '{opp['key']}': {old_values} → {opp['proposed']}"
                    )
                    applied_count += 1
                    print(f"   ✅ Applied consolidation for **{opp['key']}**")
                    break
                elif choice in ["n", "no", "2"]:
                    print(f"   ⏭️  Skipped consolidation for **{opp['key']}**")
                    break
                elif choice in ["q", "quit"]:
                    print(
                        f"   🛑 Quitting consolidation (applied {applied_count} so far)"
                    )
                    return applied_count
                else:
                    print("   ❌ Please enter 'y' for yes, 'n' for no, or 'q' to quit")

        print(f"\n✅ Consolidation complete! Applied {applied_count} optimizations.")
        return applied_count

    def save_abbreviations(self):
        """Save the updated abbreviations to the file."""
        if not self.changes_made:
            print("📝 No changes were made - abbreviations file unchanged.")
            return False

        abbreviations_file = Path("tools/abbreviations.py")

        # Create backup
        backup_file = abbreviations_file.with_suffix(".py.backup")
        if abbreviations_file.exists():
            backup_file.write_text(abbreviations_file.read_text())
            print(f"💾 Created backup: {backup_file}")

        # Generate new abbreviations file content
        content = self._generate_abbreviations_file_content()

        # Write new content
        abbreviations_file.write_text(content)
        print(f"✅ Updated abbreviations saved to: {abbreviations_file}")

        # Show summary of changes
        print("\n📋 Summary of changes made:")
        for i, change in enumerate(self.changes_made, 1):
            print(f"  {i}. {change}")

        return True

    def _generate_abbreviations_file_content(self) -> str:
        """Generate the content for the updated abbreviations file."""
        lines = [
            "#!/usr/bin/env python3",
            '"""',
            "Abbreviations dictionary for WDS enum generation.",
            "",
            "This file contains the master abbreviation mappings used by the SubstitutionEngine",
            "for generating concise enum identifiers. The abbreviations are organized by category",
            "and follow morphological extension principles.",
            "",
            "IMPORTANT: This file was automatically updated by the Interactive Abbreviation Manager.",
            "           Manual edits should be made carefully to maintain alphabetical order",
            "           and avoid conflicts.",
            '"""',
            "",
            "DEFAULT_ABBREVIATIONS = {",
        ]

        # Process abbreviations in the same order as original file
        # (This is a simplified version - would need full parsing for exact section preservation)
        for key in sorted(self.abbreviations.keys()):
            values = self.abbreviations[key]
            if len(values) == 1:
                lines.append(f'    "{key}": ["{values[0]}"],')
            else:
                values_str = ", ".join(f'"{v}"' for v in sorted(values))
                lines.append(f'    "{key}": [{values_str}],')

        lines.extend(["}", ""])

        return "\n".join(lines)


def main():
    """Main interactive abbreviation management interface."""
    print("🔧 Interactive Abbreviation Management System")
    print("=" * 60)
    print("📋 This tool helps you manage and enhance the abbreviation system with:")
    print("   • Morphological consolidation opportunities")
    print("   • New abbreviations from word tracking analysis")
    print("   • Quality validation and conflict resolution")
    print()

    manager = InteractiveAbbreviationManager()
    total_changes = 0

    # Check for existing word tracking data
    tracking_files = [
        Path("scratch/word_tracking_data.json"),
        Path("scratch/unified_word_tracking_data.json"),
        Path("scratch/test_analysis/sample_word_tracking.json"),
    ]

    word_tracker = None
    for tracking_file in tracking_files:
        if tracking_file.exists():
            print(f"📂 Found word tracking data: {tracking_file}")
            word_tracker = manager.load_word_tracking_data(tracking_file)
            if word_tracker:
                break

    while True:
        print("\n🔧 ABBREVIATION MANAGEMENT MENU")
        print("=" * 50)
        print("1. 🎯 Check and apply consolidation opportunities")
        print("2. 💡 Add abbreviations from word tracking data")
        print("3. 📊 Show current abbreviation statistics")
        print("4. 💾 Save changes and exit")
        print("5. 🚪 Exit without saving")

        if word_tracker:
            print(
                f"\n📊 Word tracking data loaded: {len(word_tracker.word_stats)} words"
            )
        else:
            print("\n⚠️  No word tracking data available")
            print("   Run enum generation with --track-words to collect data")

        if manager.changes_made:
            print(f"\n📝 Pending changes: {len(manager.changes_made)}")

        choice = input("\nSelect option [1-5]: ").strip()

        if choice == "1":
            changes = manager.interactive_consolidation_implementation()
            total_changes += changes
        elif choice == "2":
            if word_tracker:
                candidates = manager.show_abbreviation_opportunities(word_tracker)
                if candidates:
                    changes = manager.interactive_add_abbreviations(candidates)
                    total_changes += changes
            else:
                print("❌ No word tracking data available")
                print("   Run: python tools/wds_enum_gen.py --track-words")
        elif choice == "3":
            print("\n📊 ABBREVIATION STATISTICS")
            print(f"   Total abbreviation keys: {len(manager.abbreviations)}")
            total_values = sum(len(values) for values in manager.abbreviations.values())
            print(f"   Total abbreviated terms: {total_values}")
            multi_value_keys = sum(
                1 for values in manager.abbreviations.values() if len(values) > 1
            )
            print(f"   Multi-value keys: {multi_value_keys}")
            if manager.changes_made:
                print(f"   Pending changes: {len(manager.changes_made)}")
        elif choice == "4":
            if manager.save_abbreviations():
                print(f"\n🎉 Successfully saved {total_changes} changes!")
            print("👋 Goodbye!")
            break
        elif choice == "5":
            if manager.changes_made:
                confirm = (
                    input("⚠️  You have unsaved changes. Exit anyway? [y/n]: ")
                    .strip()
                    .lower()
                )
                if confirm not in ["y", "yes"]:
                    continue
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()
