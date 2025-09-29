#!/usr/bin/env python3
"""
Empty File Checker and Cleanup Tool

This tool scans the codebase for empty files, provides a summary,
and offers interactive deletion with safety checks.

Usage:
    python tools/check_empty_files.py [--dry-run] [--include-hidden] [--exclude-dirs DIR1,DIR2]
"""

import os
import sys
from pathlib import Path
from typing import Generator
import argparse


class EmptyFileChecker:
    """Utility class to find and manage empty files in the codebase."""

    def __init__(
        self,
        root_path: Path,
        include_hidden: bool = False,
        exclude_dirs: list[str] | None = None,
        include_intentionally_empty: bool = False,
    ):
        self.root_path = root_path
        self.include_hidden = include_hidden
        self.include_intentionally_empty = include_intentionally_empty
        self.exclude_dirs = set(exclude_dirs or [])

        # Default directories to exclude (can be overridden)
        self.default_exclude_dirs = {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".mypy_cache",
            ".tox",
            "build",
            "dist",
            "*.egg-info",
            ".coverage",
        }

        # Files that are intentionally empty and should be ignored
        self.intentionally_empty_files = {
            "py.typed",  # PEP 561 - indicates package supports type checking
            "__init__.py",  # Python package markers (often empty)
            ".gitkeep",  # Git placeholder for empty directories
            ".keep",  # Generic placeholder for empty directories
            "PLACEHOLDER",  # Common placeholder file
            "placeholder.txt",  # Another common placeholder
            ".placeholder",  # Hidden placeholder
        }

        # Add user-specified exclusions
        self.exclude_dirs.update(self.default_exclude_dirs)

    def _should_skip_directory(self, dir_path: Path) -> bool:
        """Check if directory should be skipped based on exclusion rules."""
        dir_name = dir_path.name

        # Skip hidden directories unless explicitly included
        if not self.include_hidden and dir_name.startswith("."):
            return True

        # Skip excluded directories
        if dir_name in self.exclude_dirs:
            return True

        # Skip directories matching patterns (like *.egg-info)
        for pattern in self.exclude_dirs:
            if "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(dir_name, pattern):
                    return True

        return False

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped based on rules."""
        # Skip hidden files unless explicitly included
        if not self.include_hidden and file_path.name.startswith("."):
            return True

        # Skip files that are intentionally empty (unless explicitly included)
        if (
            not self.include_intentionally_empty
            and file_path.name in self.intentionally_empty_files
        ):
            return True

        return False

    def find_empty_files(self) -> Generator[Path, None, None]:
        """
        Recursively find all empty files in the codebase.

        Yields:
            Path objects for empty files
        """
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Filter out excluded directories in-place
            dirs[:] = [
                d for d in dirs if not self._should_skip_directory(root_path / d)
            ]

            for file in files:
                file_path = root_path / file

                if self._should_skip_file(file_path):
                    continue

                try:
                    if file_path.is_file() and file_path.stat().st_size == 0:
                        yield file_path
                except (OSError, IOError):
                    # Skip files we can't read (permissions, etc.)
                    continue

    def categorize_empty_files(self, empty_files: list[Path]) -> dict[str, list[Path]]:
        """
        Categorize empty files by type/location for better organization.

        Args:
            empty_files: List of empty file paths

        Returns:
            Dictionary mapping categories to file lists
        """
        categories: dict[str, list[Path]] = {
            "Python Files": [],
            "Test Files": [],
            "Documentation": [],
            "Configuration": [],
            "Data Files": [],
            "Other": [],
        }

        for file_path in empty_files:
            relative_path = file_path.relative_to(self.root_path)

            if file_path.suffix == ".py":
                if "test" in str(relative_path).lower():
                    categories["Test Files"].append(file_path)
                else:
                    categories["Python Files"].append(file_path)
            elif file_path.suffix in {".md", ".rst", ".txt"}:
                categories["Documentation"].append(file_path)
            elif file_path.suffix in {
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
            }:
                categories["Configuration"].append(file_path)
            elif file_path.suffix in {".csv", ".xml", ".dat"}:
                categories["Data Files"].append(file_path)
            else:
                categories["Other"].append(file_path)

        return categories

    def print_summary(self, categorized_files: dict[str, list[Path]]) -> None:
        """Print a formatted summary of empty files found."""
        total_files = sum(len(files) for files in categorized_files.values())

        if total_files == 0:
            print("✅ No empty files found in the codebase!")
            return

        print(f"📋 Found {total_files} empty files:")
        print("=" * 50)

        for category, files in categorized_files.items():
            if files:
                print(f"\n📁 {category} ({len(files)} files):")
                for file_path in sorted(files):
                    relative_path = file_path.relative_to(self.root_path)
                    print(f"  • {relative_path}")

    def interactive_cleanup(self, categorized_files: dict[str, list[Path]]) -> None:
        """
        Interactive interface for selecting which empty files to delete.

        Args:
            categorized_files: Dictionary of categorized empty files
        """
        total_files = sum(len(files) for files in categorized_files.values())

        if total_files == 0:
            return

        print("\n🗑️  Interactive Cleanup")
        print("=" * 30)

        files_to_delete = []

        for category, files in categorized_files.items():
            if not files:
                continue

            print(f"\n📁 {category} ({len(files)} files)")

            # Ask about the entire category first
            while True:
                response = (
                    input(f"Delete all {category.lower()}? (y/n/s for selective): ")
                    .lower()
                    .strip()
                )
                if response == "y":
                    files_to_delete.extend(files)
                    print(
                        f"  ✓ Marked all {len(files)} {category.lower()} for deletion"
                    )
                    break
                elif response == "n":
                    print(f"  ✗ Skipped all {category.lower()}")
                    break
                elif response == "s":
                    # Selective mode - ask about each file
                    for file_path in files:
                        relative_path = file_path.relative_to(self.root_path)
                        while True:
                            file_response = (
                                input(f"  Delete {relative_path}? (y/n): ")
                                .lower()
                                .strip()
                            )
                            if file_response == "y":
                                files_to_delete.append(file_path)
                                print("    ✓ Marked for deletion")
                                break
                            elif file_response == "n":
                                print("    ✗ Skipped")
                                break
                            else:
                                print("    Please enter 'y' or 'n'")
                    break
                else:
                    print("Please enter 'y' (yes), 'n' (no), or 's' (selective)")

        # Final confirmation and deletion
        if files_to_delete:
            print(f"\n⚠️  Final confirmation: Delete {len(files_to_delete)} files?")
            for file_path in sorted(files_to_delete):
                relative_path = file_path.relative_to(self.root_path)
                print(f"  • {relative_path}")

            while True:
                final_response = (
                    input("\nProceed with deletion? (yes/no): ").lower().strip()
                )
                if final_response in ["yes", "y"]:
                    self._delete_files(files_to_delete)
                    break
                elif final_response in ["no", "n"]:
                    print("❌ Deletion cancelled by user")
                    break
                else:
                    print("Please enter 'yes' or 'no'")
        else:
            print("\n✅ No files selected for deletion")

    def _delete_files(self, files_to_delete: list[Path]) -> None:
        """
        Delete the specified files with error handling.

        Args:
            files_to_delete: List of file paths to delete
        """
        deleted_count = 0
        errors = []

        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                relative_path = file_path.relative_to(self.root_path)
                print(f"  ✅ Deleted: {relative_path}")
            except (OSError, IOError) as e:
                relative_path = file_path.relative_to(self.root_path)
                error_msg = f"Failed to delete {relative_path}: {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")

        print(
            f"\n📊 Summary: {deleted_count}/{len(files_to_delete)} files deleted successfully"
        )

        if errors:
            print(f"\n⚠️  {len(errors)} errors occurred:")
            for error in errors:
                print(f"  • {error}")


def main():
    """Main entry point for the empty file checker."""
    parser = argparse.ArgumentParser(
        description="Check for empty files in the codebase and optionally delete them"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show empty files, don't offer deletion",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories",
    )
    parser.add_argument(
        "--include-intentionally-empty",
        action="store_true",
        help="Include files that are intentionally empty (py.typed, __init__.py, etc.)",
    )
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        help="Comma-separated list of additional directories to exclude",
    )

    args = parser.parse_args()

    # Determine project root (where this script is run from)
    current_path = Path.cwd()
    project_root = current_path

    # If we're in the tools directory, go up one level
    if current_path.name == "tools":
        project_root = current_path.parent

    print(f"🔍 Scanning for empty files in: {project_root}")

    if not args.include_intentionally_empty:
        print(
            "📝 Note: Excluding intentionally empty files (py.typed, __init__.py, etc.)"
        )
        print("    Use --include-intentionally-empty to include them")

    # Parse exclude directories
    exclude_dirs = None
    if args.exclude_dirs:
        exclude_dirs = [d.strip() for d in args.exclude_dirs.split(",")]

    # Initialize checker and find empty files
    checker = EmptyFileChecker(
        root_path=project_root,
        include_hidden=args.include_hidden,
        exclude_dirs=exclude_dirs,
        include_intentionally_empty=args.include_intentionally_empty,
    )

    try:
        print("⏳ Searching for empty files...")
        empty_files = list(checker.find_empty_files())
        categorized_files = checker.categorize_empty_files(empty_files)

        # Print summary
        checker.print_summary(categorized_files)

        # Interactive cleanup unless dry run
        if not args.dry_run:
            total_files = sum(len(files) for files in categorized_files.values())
            if total_files > 0:
                print(
                    "\n💡 Use --dry-run to only show files without offering deletion"
                )
                checker.interactive_cleanup(categorized_files)
        else:
            print("\n🔍 Dry run mode - no files will be deleted")

    except KeyboardInterrupt:
        print("\n\n⛔ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
