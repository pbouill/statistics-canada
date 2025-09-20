#!/usr/bin/env python3
"""
Statistics Canada Package - Main Tool Interface

This script provides easy access to all core package management tools:
- Enum generation (geographic and WDS)  
- Abbreviation management and optimization
- Word tracking and analysis
- Debug utilities

Usage: python tools/main.py [action]
"""

import sys
import os
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header():
    """Print the main tool interface header."""
    print("\n" + "=" * 60)
    print("🇨🇦 STATISTICS CANADA PACKAGE - MAIN TOOL INTERFACE")  
    print("=" * 60)

def print_menu():
    """Print the main menu options."""
    print("\n📋 AVAILABLE ACTIONS:")
    print("-" * 30)
    print("1. 🏗️  Generate all enums (geographic + WDS)")
    print("2. 🗺️  Generate geographic enums only") 
    print("3. 📊 Generate WDS enums only")
    print("4. 🔤 Manage abbreviations (interactive)")
    print("5. 📈 Track words across all generators")
    print("6. 🧪 Run debug/analysis tools")
    print("7. ❓ Show help for specific tools")
    print("8. 🚪 Exit")

def run_geographic_enums():
    """Generate geographic enums from census data."""
    print("\n🏗️ Generating geographic enums from census data...")
    subprocess.run([sys.executable, "tools/generate_enums.py"], cwd=project_root)

def run_wds_enums():
    """Generate WDS enums (product IDs and code sets)."""
    print("\n📊 Generating WDS enums...")
    subprocess.run([sys.executable, "tools/wds_enum_gen.py", "--type", "all", "--verbose"], cwd=project_root)

def run_all_enums():
    """Generate all enums (geographic + WDS)."""
    print("\n🏗️ Generating ALL enums (geographic + WDS)...")
    run_geographic_enums()
    run_wds_enums()

def run_abbreviation_manager():
    """Run the interactive abbreviation management system."""
    print("\n🔤 Starting interactive abbreviation manager...")
    print("   This tool helps you:")
    print("   • Find consolidation opportunities")
    print("   • Add new abbreviations from word tracking")
    print("   • Validate morphological coverage")
    print("   • Quality check abbreviation dictionary")
    subprocess.run([sys.executable, "tools/interactive_abbreviation_manager.py"], cwd=project_root)

def run_word_tracking():
    """Run word tracking across all enum generators."""
    print("\n📈 Running word tracking across all enum generators...")
    print("   This will collect word frequency data from:")
    print("   • WDS Product ID enums")  
    print("   • WDS Code Set enums")
    print("   • Geographic enums")
    subprocess.run([sys.executable, "tools/unified_enum_processor.py", "--track-words"], cwd=project_root)

def show_debug_tools():
    """Show available debug and analysis tools."""
    print("\n🧪 DEBUG AND ANALYSIS TOOLS:")
    print("-" * 30)
    print("Available in scratch/ directory:")
    scratch_dir = project_root / "scratch"
    debug_tools = [f for f in scratch_dir.glob("*.py") if f.name.startswith(("debug_", "wds_", "population_"))]
    
    for tool in sorted(debug_tools):
        print(f"   • {tool.name}")
    
    print(f"\nTo run a debug tool: cd scratch && python {debug_tools[0].name if debug_tools else 'tool_name.py'}")
    print("Note: Debug tools are in scratch/ to keep main tools/ directory clean")

def show_tool_help():
    """Show help for specific tools."""
    print("\n❓ TOOL-SPECIFIC HELP:")
    print("-" * 25)
    print("• Geographic enums:     python tools/generate_enums.py --help")
    print("• WDS enums:           python tools/wds_enum_gen.py --help") 
    print("• Abbreviations:       python tools/interactive_abbreviation_manager.py --help")
    print("• Word tracking:       python tools/unified_enum_processor.py --help")
    print("• Individual WDS:      python tools/wds_productid_enum_gen.py --help")
    print("                       python tools/wds_code_enum_gen.py --help")

def main():
    """Main interface loop."""
    print_header()
    
    # If command line argument provided, run directly
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action in ["all", "enums"]:
            run_all_enums()
        elif action == "geo":
            run_geographic_enums()
        elif action == "wds":
            run_wds_enums()
        elif action in ["abbrev", "abbreviations"]:
            run_abbreviation_manager()
        elif action in ["track", "words"]:
            run_word_tracking()
        elif action == "debug":
            show_debug_tools()
        elif action == "help":
            show_tool_help()
        else:
            print(f"❌ Unknown action: {action}")
            print("Available: all, geo, wds, abbrev, track, debug, help")
        return
    
    # Interactive menu
    while True:
        print_menu()
        try:
            choice = input("\n🎯 Select an action [1-8]: ").strip()
            
            if choice == "1":
                run_all_enums()
            elif choice == "2":
                run_geographic_enums()  
            elif choice == "3":
                run_wds_enums()
            elif choice == "4":
                run_abbreviation_manager()
            elif choice == "5":
                run_word_tracking()
            elif choice == "6":
                show_debug_tools()
            elif choice == "7":
                show_tool_help()
            elif choice == "8":
                print("\n👋 Goodbye!")
                break
            else:
                print(f"❌ Invalid choice: {choice}. Please select 1-8.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
