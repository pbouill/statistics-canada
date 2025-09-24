from typing import Optional

try:
    from ._version import __version__    # type: ignore[attr-defined, missing-imports, import-not-found]
except ImportError:
    __version__: Optional[str] = None    # type: ignore[no-redef]

try:
    from ._version import __build_time__  # type: ignore[attr-defined, missing-imports, import-not-found]
except ImportError:
    __build_time__: Optional[str] = None  # type: ignore[no-redef]

# WDS Client (unified with all functionality)
from .wds.client import Client as WDSClient

# Geographic entities  
from .wds.geographic import GeographicEntity

# WDS Enums for status interpretation
from .enums.auto.wds.status import Status
from .enums.auto.wds.symbol import Symbol
from .enums.auto.wds.scalar import Scalar

__all__ = [
    '__version__',
    '__build_time__',
    # Primary interface - unified client
    'WDSClient',
    'GeographicEntity',
    # WDS Enums
    'Status',
    'Symbol', 
    'Scalar',
]