import setuptools


def get_package_name_version() -> tuple[str, str]:
    """
    Get the package name and version from the current version info.
    """
    from package_info import VersionInfo
    current_version = VersionInfo.get_latest()
    return current_version.package_name, current_version.version


if __name__ == '__main__':
    package_name, version = get_package_name_version()
    setuptools.setup(
        package_dir={package_name: package_name},
        version=version,
    )
