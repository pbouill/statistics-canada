data: Dict[str, Union[int, str]] = {}                          # � WRONG
data: dict[str, int | str] = {}                                # ✅ CORRECT

# Statistics Canada Python Bindings - AI Agent Instructions

## Architecture & Directory Structure

- **Core package**: `statscan/` (submodules: `wds/` async API client, `enums/` auto-generated geographic enums, `sdmx/` legacy models, `util/` utilities)
- **Code generation**: `tools/` (core logic), `tools/cli/` (CLI entry points, no business logic)
- **Testing**: All tests in `tests/` (pytest only, use `test_*.py`), fixtures in `tests/data/`
- **Examples**: Usage demos in `examples/` (never validate functionality)
- **Scratchpad**: Debug, analysis, and temporary outputs in `scratch/` (never versioned)
- **Documentation**: Official docs in `docs/`, visual pipeline charts in `docs/charts/`

## Key Development Workflows

- **Environment**: Python 3.12+ required (3.14 preferred). Always activate venv: `source .venv/bin/activate`
- **Install**: `pip install -r requirements.dev.txt` (editable mode)
- **Build**: `python -m build --no-isolation` (version auto-generated in `_version.py`)
- **Test**: `python -m pytest tests/ -v` (all tests must be pytest-compatible)
- **Code quality**: ALL Python code must pass both linters before commit:
  - Ruff linting: `ruff check --fix .` (auto-fixes most issues)
  - Type checking: `mypy --exclude-gitignore --show-error-codes --show-traceback .`
  - Pre-commit hook runs both automatically (see `tools/git/pre-commit.sh`)
  - **IMPORTANT**: Only run linters when editing Python files (`.py`). Skip for config/docs (`.toml`, `.yml`, `.md`, etc.)
- **Code generation**:
  - Geographic enums: `python tools/generate_enums.py` (never edit `enums/auto/` directly)
  - WDS enums: `python tools/cli/wds_enum_gen.py --type all --verbose`
  - Abbreviation management: `python tools/cli/interactive_abbreviation_manager.py`
  - Word tracking: `python tools/cli/unified_enum_processor.py --track-words`

## File Organization Rules

- **Never create files in root**. Use subdirectories:
  - `tests/` for validation (pytest only)
  - `examples/` for demos
  - `scratch/` for debug/temporary
  - `tools/` for production codegen
  - `docs/` for documentation
- **Common violations**: No Python scripts in `tests/data/`, no demo/debug in `tools/`, no generated outputs in root

## Project-Specific Patterns

- **Async API**: All WDS operations are async. Use:
  ```python
  from statscan.wds.client import Client
  async def get_data():
      client = Client()
      return await client.get_cube_metadata(product_id=123)
  # Run with: asyncio.run(get_data())
  ```
- **Geographic enums**: Inherit by containment (see `enums/geocode/`). Use auto-generated files only.
- **Abbreviation system**: Managed via `tools/abbreviations.py`, `substitution.py`, and CLI tools. Always validate with `tools/review_abbreviations.py` before commit.
- **Type annotations**: Use Python 3.12+ native types (e.g., `list[str]`, `str | None`). Never use legacy `List`, `Dict`, `Optional`, etc.
- **PEP 695 syntax**: Use new-style generic type parameters (`def func[T](cls: type[T], ...)`) for Python 3.12+ compatibility.
- **Code style enforcement**:
  - **88-character line limit** (configurable in `pyproject.toml`)
  - **Google-style docstrings** (D100-D417 rules enforced)
  - **Imperative mood** in docstrings ("Get data", not "Gets data")
  - **No bare except-pass blocks** (S110): Use logging instead
    ```python
    # ❌ WRONG
    except Exception:
        pass
    
    # ✅ CORRECT
    except Exception as e:
        logger.warning("Operation failed: %s", e)
    ```
  - **Named constants** for magic values (PLR2004)
  - **Import sorting** (I001): stdlib → third-party → local

## Integration & Automation

- **WDS API**: Reference [WDS User Guide](https://www.statcan.gc.ca/en/developers/wds/user-guide) for endpoint specs and troubleshooting. Base URL in `statscan/url.py`.
- **Changelog automation**: Managed by `seawall-changelog-bot` via `.github/workflows/dev-changelog.yml` (see `/docs/charts/` for visual pipeline docs).
- **Release pipeline**: 5-stage automation in `.github/workflows/release-pipeline-new.yml`, rollback logic included.
- **Visual documentation**: All workflow changes must be reflected in `/docs/charts/workflow_diagram.md` and related files.

## Testing & Validation

- **Test isolation**: Each test creates its own WDS client instance.
- **Fixture system**: Use `TestFixtureManager` and StrEnum classes for path management.
- **Execution order**: Run network tests first to generate fixtures, then functionality tests.
- **Markers**: Use `@pytest.mark.network` for network tests, `@pytest.mark.asyncio` for async tests.
- **Network tests**: By default, `pytest` skips network tests to avoid timeouts. Use `pytest --network` to run all tests including network tests.

## Workflow Testing with Act

- **Local workflow testing**: Use `act` to test GitHub Actions workflows locally before pushing
- **Configuration**: `.actrc` contains required settings:
  - `--container-architecture linux/amd64` for platform compatibility
  - `-P ubuntu-latest=catthehacker/ubuntu:act-latest` for image mapping
  - `--env PYTHON_GIL=1` to fix Python 3.14 compatibility (act sets `PYTHON_GIL=0` by default, which isn't supported)
- **Test commands**:
  - List jobs: `act pull_request --list`
  - Run specific job: `act pull_request -j qa-qc`
  - Run with verbose output: `act pull_request -j qa-qc -v`
- **Expected limitations**:
  - Git push operations will fail (authentication issue) - this is normal for local testing
  - Secrets/tokens won't work unless explicitly configured
  - Some GitHub-specific features may behave differently
- **Best practice**: Test workflows locally with `act` before pushing to catch syntax errors and logic issues early

## Quick Reference

- **Setup**:
  ```bash
  source .venv/bin/activate
  pip install -r requirements.dev.txt
  ```
- **Run examples**:
  ```bash
  python examples/client_overview.py
  python examples/basic_usage.py
  ```
- **Debug/analysis**:
  Place all scripts in `scratch/`, e.g. `scratch/debug_api_response.py`

## AI Agent Protocols

- Always cite info sources (e.g., copilot-instructions.md, README.md, docs/charts)
- Update both code and visual docs for workflow/architecture changes
- Cross-reference workflow files and diagrams for accuracy
- Use color-coded status: 🟢 Active, 🟠 Ready, 🔵 Proposed, ⚪ Legacy
- **CRITICAL: All code edits MUST be ruff and mypy compliant**:
  - Run `ruff check --fix .` after making changes
  - Run `mypy --exclude-gitignore --show-error-codes --show-traceback .` to verify types
  - Pre-commit hook will reject non-compliant code
  - Maintain 100% compliance: 0 ruff errors, 0 mypy errors

---
For full architecture, workflow, and troubleshooting details, see `/docs/charts/README.md` and `/docs/charts/workflow_diagram.md`.
