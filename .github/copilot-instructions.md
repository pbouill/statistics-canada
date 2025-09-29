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

- **Environment**: Python 3.11+ required. Always activate venv: `source .venv/bin/activate`
- **Install**: `pip install -r requirements.dev.txt` (editable mode)
- **Build**: `python -m build --no-isolation` (version auto-generated in `_version.py`)
- **Test**: `python -m pytest tests/ -v` (all tests must be pytest-compatible)
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
- **Type annotations**: Use Python 3.11+ native types (e.g., `list[str]`, `str | None`). Never use legacy `List`, `Dict`, `Optional`, etc.

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

---
For full architecture, workflow, and troubleshooting details, see `/docs/charts/README.md` and `/docs/charts/workflow_diagram.md`.
