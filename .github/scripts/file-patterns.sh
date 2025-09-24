#!/bin/bash
# Shared file pattern definitions for GitHub workflows
# Usage: source .github/scripts/file-patterns.sh

# Package-relevant file patterns (triggers builds/releases)
is_package_file() {
    local file="$1"
    
    if [[ "$file" =~ ^statscan/ ]] || \
       [[ "$file" =~ ^pyproject\.toml$ ]] || \
       [[ "$file" =~ ^setup\.py$ ]] || \
       [[ "$file" =~ ^requirements.*\.txt$ ]] || \
       [[ "$file" =~ ^README\.md$ ]] || \
       [[ "$file" =~ ^LICENSE$ ]]; then
        return 0  # true
    else
        return 1  # false
    fi
}

# Infrastructure-only file patterns (skip builds/releases)
is_infrastructure_file() {
    local file="$1"
    
    if [[ "$file" =~ ^\.github/ ]] || \
       [[ "$file" =~ ^docs/ ]] || \
       [[ "$file" =~ ^tools/ ]] || \
       [[ "$file" =~ ^examples/ ]] || \
       [[ "$file" =~ ^scratch/ ]] || \
       [[ "$file" =~ ^tests/.*\.py$ ]]; then
        return 0  # true
    else
        return 1  # false
    fi
}

# Combined check for whether changes should trigger package operations
should_trigger_package_operations() {
    local changed_files="$1"
    
    for file in $changed_files; do
        if [ -z "$file" ]; then continue; fi
        
        if is_package_file "$file"; then
            echo "true"
            return 0
        fi
        
        if is_infrastructure_file "$file"; then
            continue
        fi
        
        # Unknown file type - be conservative
        echo "true"
        return 0
    done
    
    echo "false"
    return 1
}

# GitHub paths: configuration for workflow triggers
# Can be used in workflow files as: paths: $(cat .github/scripts/package-paths.txt)
generate_github_paths() {
    cat << 'EOF'
- 'statscan/**'
- 'pyproject.toml'
- 'setup.py'
- 'requirements*.txt'
- 'README.md'
- 'LICENSE'
EOF
}
