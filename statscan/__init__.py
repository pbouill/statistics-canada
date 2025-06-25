from typing import Optional

try:
    from ._version import __version__    # type: ignore[attr-defined, missing-imports, import-not-found]
except ImportError:
    __version__: Optional[str] = None    # type: ignore[no-redef]

try:
    from ._version import __build_time__  # type: ignore[attr-defined, missing-imports, import-not-found]
except ImportError:
    __build_time__: Optional[str] = None  # type: ignore[no-redef]