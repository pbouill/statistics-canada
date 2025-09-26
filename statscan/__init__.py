from importlib.metadata import packages_distributions, version
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# Explicitly declare the public API for this module
__all__ = ["__version__"]


def _initialize_version() -> str:
    """
    Initializes the package version.

    Tries to get the version from installed package metadata first.
    Falls back to reading from a local _version.py file for development.
    """
    try:
        # This is the primary method: get the version from installed package metadata
        dist_map = packages_distributions()
        distribution_name = dist_map[__name__][0]
        return version(distribution_name)
    except (KeyError, IndexError):
        # This is the fallback for development scenarios
        repo_root = Path(__file__).parent.parent
        version_file_path = repo_root / "_version.py"
        if not version_file_path.exists():
            return 'unknown-no-version-file'

        spec = spec_from_file_location("_version", version_file_path)
        if not spec or spec.loader is None:
            return 'unknown-no-spec-or-loader'

        try:
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.__version__
        except AttributeError:
            return 'unknown-no-version-attribute'
        except Exception:
            return 'unknown-exec-error'
        
__version__ = _initialize_version()
