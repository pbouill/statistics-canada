#!/bin/sh
#
# This pre-commit hook runs a series of quality checks:
# 1. Ruff: Lints and auto-fixes Python code.
# 2. Mypy: Performs static type checking.
# 3. pip-audit: Checks for known vulnerabilities in dependencies.
# 4. Bandit: Scans for common security issues in the code.
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

print_info "🚀 Starting pre-commit checks..."
echo "-------------------------------------"

# 1. Run Ruff Linter and Auto-fixer
print_info "1/4: Running Ruff..."
ruff check --fix .
# Check the exit code of the ruff command
if [ $? -ne 0 ]; then
    print_error "Ruff found issues. Please review and fix them before committing."
    exit 1
fi

# IMPORTANT: Add any files that were auto-fixed by `ruff` to the staging area.
# This ensures that the automatic fixes are included in the commit.
print_info "Staging files auto-fixed by Ruff..."
git add . > /dev/null 2>&1

print_success "✅ Ruff check passed."
echo

# 2. Run Mypy for Static Type Checking
print_info "2/4: Running Mypy..."
mypy --exclude-gitignore --show-error-codes --show-traceback .
if [ $? -ne 0 ]; then
    print_error "Mypy found type errors. Please correct them before committing."
    exit 1
fi
print_success "✅ Mypy check passed."
echo

# 3. Run pip-audit for Dependency Vulnerabilities
print_info "3/4: Running pip-audit..."
if [ -f "requirements.txt" ]; then
    pip-audit -v -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "pip-audit found vulnerabilities in your dependencies. Please review the report."
        exit 1
    fi
    print_success "✅ pip-audit check passed."
else
    # If no requirements.txt, just show a warning and continue.
    print_info "   -> requirements.txt not found, skipping pip-audit."
fi
echo

# 4. Run Bandit for Security Analysis
print_info "4/4: Running Bandit..."
# Create the output directory for the report if it doesn't exist
mkdir -p scratch
bandit --exclude=./.venv . -r -v -lll -o scratch/bandit-report.json -f json
if [ $? -ne 0 ]; then
    print_error "Bandit found potential security issues. Review the report in scratch/bandit-report.json"
    exit 1
fi
print_success "✅ Bandit check passed."
echo "-------------------------------------"
print_success "🎉 All checks passed! Proceeding with commit."

exit 0
