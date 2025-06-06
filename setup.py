import sys
import setuptools
from pathlib import Path
from contextlib import contextmanager


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
    import package_info
    current_version = package_info.VersionInfo.get_latest()

setuptools.setup(
    package_dir={current_version.package_name: current_version.package_name},
    version=current_version.version,
)
