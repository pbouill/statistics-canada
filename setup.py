from calendar import c
import setuptools

try:
    import package_info
except ModuleNotFoundError as mnfe:
    import importlib.util
    from pathlib import Path
    try:
        if (spec := importlib.util.spec_from_file_location(name='package_info', location=Path(__file__).parent / 'package_info.py')) is None:
            raise ImportError("Cannot determine package_info module spec.") from mnfe
        if spec.loader is None:
            raise ImportError(f"Cannot determine spec loader for package_info module. {spec=}") from mnfe
        package_info = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(package_info)
    except Exception as e:
        raise ImportError(f"Cannot load package_info module. {e=}") from e

current_version = package_info.VersionInfo.get_latest()

setuptools.setup(
    package_dir={current_version.package_name: current_version.package_name},
    version=current_version.version,
)