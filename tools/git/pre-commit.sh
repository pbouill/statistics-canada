#!/bin/sh
#
# Optimized pre-commit hook that runs quality checks only when needed:
# 1. Ruff: Lints, auto-fixes, and checks security (S rules) on Python code (only on .py files).
# 2. Mypy: Performs static type checking (only on .py files, incremental mode).
# 3. pip-audit: Checks for known vulnerabilities (only if requirements changed).
#
# Performance optimizations:
# - Only runs Python linters when .py files are staged
# - Uses mypy's incremental cache for faster checks
# - Skips dependency audits if requirements.txt unchanged
# - Ruff's S rules (bandit-compatible) check security, Python 3.14 compatible
#
# If any of these checks fail, the commit will be aborted.

# --- Helper Functions for Colored Output ---
# Use these to make the output easier to read.
print_info() {
    # Blue color for informational messages
    printf "\033[34m%s\033[0m\n" "$1"
}

print_success() {
    # Green color for success messages
    printf "\033[32m%s\033[0m\n" "$1"
}

print_error() {
    # Red color for error messages
    printf "\033[31m%s\033[0m\n" "$1"
}


# --- Main Script ---

# Activate Python virtual environment if available
if [ -d ".venv" ]; then
    . .venv/bin/activate
    print_info "Activated Python virtual environment (.venv)"
fi

# Get list of staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
# Check if requirements.txt is being modified
REQUIREMENTS_CHANGED=$(git diff --cached --name-only --diff-filter=ACM | grep -c 'requirements.*\.txt$')

# If no Python files are staged, skip Python linters
if [ -z "$STAGED_PY_FILES" ]; then
    print_success "✅ No Python files staged - skipping linters"
    print_success "🎉 Commit allowed (config/docs only)"
    exit 0
fi

print_info "🚀 Starting pre-commit checks for Python files..."
print_info "   Files to check: $(echo "$STAGED_PY_FILES" | wc -l) Python file(s)"
echo "-------------------------------------"

# 1. Run Ruff Linter and Auto-fixer (includes security checks via S rules)
print_info "1/3: Running Ruff (includes security checks)..."
echo "$STAGED_PY_FILES" | xargs ruff check --fix
# Check the exit code of the ruff command
if [ $? -ne 0 ]; then
    print_error "Ruff found issues. Please review and fix them before committing."
    exit 1
fi

# IMPORTANT: Add any files that were auto-fixed by `ruff` to the staging area.
# This ensures that the automatic fixes are included in the commit.
print_info "Staging files auto-fixed by Ruff..."
echo "$STAGED_PY_FILES" | xargs git add > /dev/null 2>&1

print_success "✅ Ruff check passed."
echo

# 2. Run Mypy for Static Type Checking (uses config from pyproject.toml)
print_info "2/3: Running Mypy..."
# Mypy now uses settings from [tool.mypy] in pyproject.toml
# - show_error_codes = true
# - show_traceback = true
# - exclude_gitignore = true
# - incremental = true
echo "$STAGED_PY_FILES" | xargs mypy
if [ $? -ne 0 ]; then
    print_error "Mypy found type errors. Please correct them before committing."
    print_info "Tip: Run 'mypy .' to see all errors"
    exit 1
fi
print_success "✅ Mypy check passed."
echo

# 3. Run pip-audit for Dependency Vulnerabilities (only if requirements changed)
if [ "$REQUIREMENTS_CHANGED" -gt 0 ]; then
    print_info "3/3: Running pip-audit (requirements changed)..."
    if [ -f "requirements.txt" ]; then
        pip-audit -v -r requirements.txt
        if [ $? -ne 0 ]; then
            print_error "pip-audit found vulnerabilities. Please review the report."
            exit 1
        fi
        print_success "✅ pip-audit check passed."
    else
        print_info "   -> requirements.txt not found, skipping pip-audit."
    fi
else
    print_info "3/3: Skipping pip-audit (requirements unchanged)"
    print_success "✅ pip-audit skipped (no changes)."
fi
echo "-------------------------------------"
print_success "🎉 All checks passed! Proceeding with commit."

exit 0
