# Abbreviations QA Integration Documentation

## Overview

The `tools/review_abbreviations.py` script provides comprehensive quality assurance for the abbreviations system with built-in support for CI/CD pipelines and pytest integration.

## Features

### 1. **Validation Checks**
- ✅ Alphabetical order verification (except provinces in canonical order)
- ✅ Duplicate key detection
- ✅ Duplicate value detection within and across lists
- ✅ Morphological overlap analysis using SubstitutionEngine
- ✅ Variant conflict detection between explicit and generated terms

### 2. **Consolidation Analysis**
- 💡 Identifies opportunities to consolidate multiple terms under morphological roots
- 🔍 Suggests optimizations to reduce abbreviation complexity
- 📊 Provides coverage analysis for proposed consolidations

### 3. **QA Integration Modes**

#### Interactive Mode (Default)
```bash
python tools/review_abbreviations.py
```
- Detailed output with visual indicators (✅ ❌ 💡)
- Comprehensive recommendations and next steps
- Full consolidation opportunity analysis

#### QA Mode (`--qa`)
```bash
python tools/review_abbreviations.py --qa
```
- Minimal output suitable for CI/CD logs
- Returns simple status: `PASS`, `FAIL`, `PASS_WITH_OPPORTUNITIES`, `ERROR`
- Exit codes for programmatic integration

#### Check-Only Mode (`--check-only`)
```bash
python tools/review_abbreviations.py --check-only
```
- Validation only, skips consolidation analysis
- Faster execution for strict error checking
- Can be combined with `--qa` for CI/CD validation

## Exit Codes

| Code | Status | Description |
|------|--------|-------------|
| `0` | ✅ **PASS** | All checks passed, no issues found |
| `1` | ❌ **FAIL** | Validation errors found (must be fixed) |
| `2` | ⚠️ **PASS_WITH_OPPORTUNITIES** | Consolidation opportunities available |
| `3` | 💥 **ERROR** | Critical errors (file not found, import failures) |

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Validate Abbreviations
  run: |
    python tools/review_abbreviations.py --qa --check-only
    if [ $? -eq 1 ] || [ $? -eq 3 ]; then
      echo "Abbreviations validation failed"
      exit 1
    fi
```

### Pytest Integration
```python
import subprocess
import sys

def test_abbreviations_validation():
    result = subprocess.run([
        sys.executable, "tools/review_abbreviations.py", "--qa"
    ], capture_output=True)
    
    # Accept both perfect (0) and optimization opportunities (2)
    assert result.returncode in [0, 2], f"Validation failed: {result.stdout}"
```

### Make Target
```makefile
qa-abbreviations:
	python tools/review_abbreviations.py --qa --check-only
	@echo "Abbreviations QA check completed"

.PHONY: qa-abbreviations
```

## Workflow Integration

### 1. **Development Workflow**
```bash
# Before committing changes to abbreviations.py
python tools/review_abbreviations.py
```

### 2. **CI/CD Validation**
```bash
# In automated pipelines
python tools/review_abbreviations.py --qa --check-only
```

### 3. **Optimization Workflow**
```bash
# Interactive optimization
python tools/resolve_morphological_conflicts.py

# Validate optimizations
python tools/review_abbreviations.py --qa
```

## Return Value Integration

The script returns a `ReviewResult` object when imported:

```python
from tools.review_abbreviations import review_abbreviations_file

# Programmatic integration
result = review_abbreviations_file(qa_mode=True, check_only=True)

print(f"Entry count: {result.entry_count}")
print(f"Errors: {len(result.errors)}")
print(f"Opportunities: {len(result.consolidation_opportunities)}")
print(f"Success: {result.success}")
print(f"Exit code: {result.exit_code}")
```

## Example Outputs

### QA Mode Success
```
PASS
```
(Exit code: 0)

### QA Mode with Opportunities
```
PASS_WITH_OPPORTUNITIES: 3 optimization opportunities
```
(Exit code: 2)

### QA Mode Failure
```
FAIL: 5 validation errors
```
(Exit code: 1)

### QA Mode Critical Error
```
ERROR: Critical validation failure
```
(Exit code: 3)

## Best Practices

1. **Pre-commit**: Run interactive mode to catch issues early
2. **CI/CD**: Use `--qa --check-only` for fast validation
3. **Optimization**: Use consolidation opportunities to improve efficiency
4. **Monitoring**: Track exit codes in automation logs
5. **Documentation**: Update this file when adding new validation checks

## Troubleshooting

### Common Issues

1. **Exit code 1**: Fix validation errors before proceeding
   - Run interactive mode for detailed error descriptions
   - Use tools/resolve_morphological_conflicts.py for automatic fixes

2. **Exit code 2**: Optional optimization available
   - Acceptable in CI/CD pipelines (not a failure)
   - Run tools/resolve_morphological_conflicts.py to optimize

3. **Exit code 3**: Critical system error
   - Check file permissions and Python environment
   - Verify all dependencies are installed

### Performance Notes

- **Interactive mode**: ~2-3 seconds for full analysis
- **QA mode**: ~1-2 seconds for validation only
- **Check-only mode**: ~1 second for strict validation
- **Memory usage**: <50MB for typical abbreviations file

## Related Tools

- `tools/resolve_morphological_conflicts.py`: Interactive consolidation implementation
- `tools/abbreviations.py`: Core abbreviations dictionary
- `tools/substitution.py`: SubstitutionEngine for morphological analysis
- `test_abbreviations_qa.py`: Example pytest integration
