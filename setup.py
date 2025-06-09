# !! Note: build in a non-isolated environment to utilize the package_info module (python -m build --no-isolation)

import sys
from pathlib import Path
import setuptools
from contextlib import contextmanager


@contextmanager
def local_imports():
    """
    Context manager to temporarily add the local directory to sys.path.
    This allows importing local modules without installing them.
    """
    original_sys_path = sys.path.copy()
    sys.path.insert(0, str(Path(__file__).parent.resolve()))
    try:
        yield
    finally:
        sys.path = original_sys_path

with local_imports():
    from package_info import VersionInfo
    current_version = VersionInfo.get_latest()


if __name__ == '__main__':
    setuptools.setup(
        package_dir={current_version.package_name: current_version.package_name},
        version=current_version.version,
    )
