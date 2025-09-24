# Test Feature for New Workflow

This is a test file to demonstrate the new dev/main branching workflow.

## What this tests:

1. **Feature branch creation**: ✅ `feature/test-new-workflow` created from `dev`
2. **PR to dev branch**: Will test changelog auto-update on merge
3. **Dev branch build**: Will test dev-specific GitHub Actions
4. **Manual promotion**: Later test merging dev → main for release

## Expected workflow:

- This PR should trigger dev-build.yml when opened
- Merging should trigger dev-changelog.yml to update CHANGELOG.md
- Dev builds should pass before allowing merge to main
- Main merge should trigger release process

**This demonstrates the improved quality control process!**
