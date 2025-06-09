import setuptools
from package_info import VersionInfo


current_version = VersionInfo.get_latest()

setuptools.setup(
    package_dir={current_version.package_name: current_version.package_name},
    version=current_version.version,
)
