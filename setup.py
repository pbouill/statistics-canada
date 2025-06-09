import sys
from pathlib import Path
from contextlib import contextmanager

import setuptools

@contextmanager
def local_syspath():
    local_path = Path(__file__).parent
    original_path = sys.path.copy()
    try:
        if str(local_path) not in sys.path:
            sys.path.insert(0, str(local_path))
        yield
    finally:
        sys.path = original_path


with local_syspath():
    from package_info import VersionInfo
    current_version = VersionInfo.get_latest()

setuptools.setup(
    package_dir={current_version.package_name: current_version.package_name},
    version=current_version.version,
)
