import sys
from pathlib import Path

# Ensure local imports work even if not installed
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# Now import package_info (which will import statscan if possible)
from package_info import VersionInfo

current_version = VersionInfo.get_latest()


if __name__ == '__main__':
    import setuptools
    setuptools.setup(
        package_dir={current_version.package_name: current_version.package_name},
        version=current_version.version,
    )
