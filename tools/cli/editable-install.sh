#!/usr/bin/env bash
# ======================================================================================
# Editable Package Installation Script
# ======================================================================================
#
# Description:
#   Intelligently installs or updates the package in editable mode.
#   - Checks if package is already installed
#   - Compares current version with repository version
#   - Only reinstalls if versions differ
#   - Provides user-friendly output
#
# Usage:
#   ./tools/cli/editable-install.sh
#
# ======================================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Editable Package Installation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo

# Get package name from pyproject.toml
PACKAGE_NAME=$(python3 -c "
import tomllib
from pathlib import Path
pyproject_path = Path('$PROJECT_ROOT') / 'pyproject.toml'
with pyproject_path.open('rb') as f:
    config = tomllib.load(f)
print(config['project']['name'])
" 2>/dev/null)

if [ -z "$PACKAGE_NAME" ]; then
    echo -e "${RED}✗ Error: Could not read package name from pyproject.toml${NC}"
    exit 1
fi

echo -e "${CYAN}📦 Package: ${NC}$PACKAGE_NAME"
echo

# Update version file to get current repository version
echo -e "${CYAN}🔍 Checking repository version...${NC}"
cd "$PROJECT_ROOT"
python build_info.py -u > /dev/null 2>&1

REPO_VERSION=$(python build_info.py -p version 2>/dev/null)
REPO_COMMIT=$(python build_info.py -p commit 2>/dev/null)
REPO_BRANCH=$(python build_info.py -p branch 2>/dev/null)

echo -e "   Repository version: ${GREEN}${REPO_VERSION}${NC}"
echo -e "   Branch: ${YELLOW}${REPO_BRANCH}${NC}"
echo -e "   Commit: ${YELLOW}${REPO_COMMIT:0:8}${NC}"
echo

# Check if package is already installed using pip
if pip show "$PACKAGE_NAME" > /dev/null 2>&1; then
    INSTALLED_VERSION=$(pip show "$PACKAGE_NAME" 2>/dev/null | grep "Version:" | awk '{print $2}')
    echo -e "${CYAN}📌 Installed version: ${NC}${INSTALLED_VERSION}"
    
    if [ "$INSTALLED_VERSION" = "$REPO_VERSION" ]; then
        echo -e "${GREEN}✓ Package is up to date${NC}"
        echo
        read -p "Reinstall anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓ Installation skipped${NC}"
            exit 0
        fi
        NEEDS_INSTALL=true
    else
        echo -e "${YELLOW}⚠ Version mismatch detected${NC}"
        NEEDS_INSTALL=true
    fi
else
    echo -e "${YELLOW}⚠ Package not currently installed${NC}"
    NEEDS_INSTALL=true
fi

if [ "$NEEDS_INSTALL" = true ]; then
    echo
    echo -e "${CYAN}🔧 Preparing for installation...${NC}"
    
    # Clean up old egg-info directories
    echo -e "   Cleaning old build artifacts..."
    find "$PROJECT_ROOT" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Uninstall existing package
    if [ "$INSTALLED_VERSION" != "NOT_INSTALLED" ]; then
        echo -e "   ${YELLOW}Uninstalling old version...${NC}"
        pip uninstall -y "$PACKAGE_NAME" > /dev/null 2>&1 || true
    fi
    
    # Install in editable mode
    echo
    echo -e "${CYAN}📥 Installing package in editable mode...${NC}"
    set +e  # Temporarily disable exit on error for pip install
    pip install -e "$PROJECT_ROOT" --quiet
    INSTALL_EXIT_CODE=$?
    set -e  # Re-enable exit on error
    
    if [ $INSTALL_EXIT_CODE -ne 0 ]; then
        # Check if it's just the "Can't uninstall" warning
        if pip show "$PACKAGE_NAME" > /dev/null 2>&1; then
            echo -e "   ${YELLOW}Note: Installation completed with warnings${NC}"
        else
            echo -e "${RED}✗ Installation failed${NC}"
            exit 1
        fi
    fi
    
    # Verify installation
    if pip show "$PACKAGE_NAME" > /dev/null 2>&1; then
        NEW_VERSION=$(pip show "$PACKAGE_NAME" 2>/dev/null | grep "Version:" | awk '{print $2}')
        
        if [ "$NEW_VERSION" = "$REPO_VERSION" ]; then
            echo
            echo -e "${GREEN}✓ Installation successful!${NC}"
            echo -e "   Installed version: ${GREEN}${NEW_VERSION}${NC}"
        else
            echo
            echo -e "${RED}✗ Installation completed but version mismatch${NC}"
            echo -e "   Expected: ${REPO_VERSION}"
            echo -e "   Got: ${NEW_VERSION}"
            exit 1
        fi
    else
        echo
        echo -e "${RED}✗ Installation failed - package not found${NC}"
        exit 1
    fi
fi

echo
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Done${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"