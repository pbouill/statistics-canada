import setuptools


def get_package_name_version() -> tuple[str, str]:
    """
    Get the package name and version from the current version info.
    """
    try:
        from package_info import VersionInfo
    except ImportError:
        from pathlib import Path
        import importlib.util
        path = Path(__file__).parent / "package_info.py"
        spec = importlib.util.spec_from_file_location("package_info", path)
        if spec is None:
            raise ImportError(f"Could not find package_info.py at {path.resolve()}")
        package_info = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Could not load package_info module from {path.resolve()}")
        spec.loader.exec_module(package_info)
        VersionInfo = package_info.VersionInfo  # type: ignore[misc]
    current_version = VersionInfo.get_latest()
    return current_version.package_name, current_version.version


if __name__ == '__main__':
    package_name, version = get_package_name_version()
    setuptools.setup(
        package_dir={package_name: package_name},
        version=version,
    )
