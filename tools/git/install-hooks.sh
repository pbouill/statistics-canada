#!/bin/sh
#
# This script installs the project's pre-commit hook by creating a
# symlink to it in the local .git/hooks directory.

# --- Configuration ---
# The source file for the hook, located within the repository.
HOOK_SOURCE="tools/git/pre-commit.sh"

# The destination path for the hook in the local git directory.
HOOK_DEST=".git/hooks/pre-commit"

# --- Helper Functions for Colored Output ---
print_info() {
    printf "\033[34m%s\033[0m\n" "$1"
}

print_success() {
    printf "\033[32m%s\033[0m\n" "$1"
}

print_error() {
    printf "\033[31m%s\033[0m\n" "$1"
}

# --- Main Script ---
print_info "Starting pre-commit hook installation..."

# Check if we are inside a Git repository
if [ ! -d ".git" ]; then
    print_error "Error: This does not appear to be a Git repository."
    print_error "Please run this script from the root of your project."
    exit 1
fi

# Check if the source hook file exists
if [ ! -f "$HOOK_SOURCE" ]; then
    print_error "Error: Source hook file not found at '$HOOK_SOURCE'."
    print_error "Please ensure the hook script is present in the repository."
    exit 1
fi

print_info "Ensuring source hook script is executable..."
chmod +x "$HOOK_SOURCE"

print_info "Creating symlink for pre-commit hook at '$HOOK_DEST'..."

# Create a relative symlink from the .git/hooks directory back to the script.
# The -f flag forces the overwrite of an existing file/symlink.
# The path is relative from the destination directory (.git/hooks).
ln -s -f "../../$HOOK_SOURCE" "$HOOK_DEST"

if [ $? -eq 0 ]; then
    print_success "✅ Pre-commit hook symlinked successfully!"
    print_info "   Any updates to '$HOOK_SOURCE' will be reflected automatically."
else
    print_error "Error: Failed to create the symlink."
    exit 1
fi

exit 0


