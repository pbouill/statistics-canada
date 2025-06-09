# This file provides basic mappings for the build process
from typing import Optional, Self, ClassVar, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, fields, Field
import logging

import statscan as base_pkg  # TODO: update

_GIT_DIR_NAME: str = '.git'

PACKAGE_NAME: str = base_pkg.__name__
PACKAGE_PATH: Path = Path(base_pkg.__file__).parent
VERSION: Optional[str] = base_pkg.__version__
VERSION_FILE: Path = PACKAGE_PATH / '_version.py'

logger  = logging.getLogger(name=__name__)


def get_git_head_ref_hash(repo_dir: Optional[Path] = None) -> tuple[str, str]:
    '''
    Get the current git commit hash and reference.
    Args:
        repo_dir (Path): The path to the git repository. If None, uses the current directory.
    Returns:
        tuple: A tuple containing the reference and commit hash.
    '''
    repo_dir = repo_dir or PACKAGE_PATH.parent
    git_path = repo_dir / _GIT_DIR_NAME
    try:
        head_path = git_path / 'HEAD'
        with head_path.open() as f:
            ref: str = f.read().strip().split(' ')[-1]
    except FileNotFoundError:
        raise FileNotFoundError(f"Git repository not found in {head_path.resolve()}. Please ensure you are in a valid git repository.")
    try:
        ref_path = git_path / ref
        with ref_path.open() as f:
            commit_hash: str = f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Git reference not found in {ref_path.resolve()}. Please ensure you are in a valid git repository.")
    return ref, commit_hash

def get_git_head_hash(repo_dir: Optional[Path] = None) -> str:
    '''
    Get the current git commit hash.
    Args:
        repo_dir (Path): The path to the git repository. If None, uses the current directory.
    Returns:
        str: The current git commit hash.
    '''
    return get_git_head_ref_hash(repo_dir=repo_dir)[1]

def create_version_info() -> dict[str, Any]:
    '''
    Get the version number and build metadata.
    Returns:
        dict: A dictionary of name-value pairs containing the version number and build metadata.
    '''
    version_time: datetime = datetime.now(tz=timezone.utc)
    return {
        '__version__': f'{version_time.year}.{version_time.month}.{version_time.day}.{version_time.hour:02d}{version_time.minute:02d}{version_time.second:02d}',
        '__build_time__': version_time,
        '__commit__': get_git_head_ref_hash(),
    }

@dataclass
class VersionInfo:
    SUPPORTED_TYPES: ClassVar = (int, float, str, bool)
    package_name: str = PACKAGE_NAME
    build_time: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    commit: str = field(default_factory=get_git_head_hash)

    @property  # type: ignore[no-redef]
    def version(self) -> str:
        return self.version_str_from_datetime(self.build_time)

    @classmethod
    def version_str_from_datetime(cls, dt: datetime) -> str:
        return f'{dt.year}.{dt.month}.{dt.day}.{dt.hour:02d}{dt.minute:02d}{dt.second:02d}'
    
    @classmethod
    def from_version_file(cls, file_path: Optional[Path] = None) -> Self:
        '''
        Load version information from a file.
        Raises ValueError if any required fields are missing from the file.
        '''
        file_path = file_path or VERSION_FILE
        kwargs: dict[str, Any] = {}
        kwargs['package_name'] = file_path.parent.name
        cls_fields: dict[str, Field] = {f.name: f for f in fields(cls)}
        
        # Set package_name from parent directory
        kwargs['package_name'] = file_path.parent.name
        # Track which fields we've found in the file
        found_fields = {'package_name'}  # package_name is always set from file path
        
        with file_path.open(mode="r") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                    
                v_type = None
                key: str
                value_str: str
                key, value_str = line.split("=", 1)  # Split only on first =
                
                if len(key_type := key.split(":")) > 1:
                    if len(key_type) > 2:
                        raise ValueError(f"Cannot parse key: {key_type[0]}. {key_type=}")
                    for t in cls.SUPPORTED_TYPES:
                        if key_type[1].strip() == t.__name__:
                            v_type = t
                            break
                    key = key_type[0]
                    
                key = key.strip().replace('__', '')
                if key == 'version':  # just a property, derived from build_time
                    continue
                    
                if (fld := cls_fields.get(key, None)) is not None:
                    value: Any
                    value_str = value_str.split("#")[0].strip().replace("'", "").replace('"', "")
                    if not isinstance((fld_type := fld.type), type):
                        raise TypeError(f"Field {key} is not a type. {fld_type=}. {value_str=}")
                    elif fld_type is datetime:
                        try:
                            value = datetime.fromisoformat(value_str)
                            kwargs[key] = value
                            found_fields.add(key)
                        except ValueError:
                            raise ValueError(f"Invalid datetime format for key {key}: {value_str}")
                    else:
                        if (fld_type != v_type) and (v_type is not None):
                            logger.warning(f"Type mismatch for key {key}. Expected {fld.type}, got {v_type}. {value_str=}")
                        try:
                            value = fld_type(value_str)
                            kwargs[key] = value
                            found_fields.add(key)
                        except (ValueError, TypeError) as e:
                            raise ValueError(f"Cannot convert value '{value_str}' to {fld_type.__name__} for field {key}: {e}")
                else:
                    logger.warning(f"Key {key} not found in {cls.__name__}. {value_str}")
        
        # Check that all required fields were found
        required_fields = {f.name for f in fields(cls)}
        missing_fields = required_fields - found_fields
        if missing_fields:
            raise ValueError(f"Missing required fields in version file {file_path}: {missing_fields}")
        
        return cls(**kwargs)

    
    def write_version_file(self, file_path: Optional[Path] = None) -> Path:
        '''
        Write the version number and build metadata to a file.
        '''
        file_path = file_path or VERSION_FILE
        with open(file=file_path, mode="w") as f:
            f.write(f"# This file is automatically generated by ../{Path(__file__).name} \n")
            f.write(f"__version__: str = '{self.version}'\n")
            for fld in fields(self):
                if fld.name == 'package_name':  # package name is derived from the version file path
                    continue
                if not isinstance(fld_type := fld.type, type):
                    raise TypeError(f"Field {fld.name} is not a type. {fld_type=}")
                v = getattr(self, fld.name)
                if isinstance(v, datetime):
                    v = v.isoformat()
                f.write(f"__{fld.name}__: {type(v).__name__} = '{str(v)}'\n")
        return file_path
    
    @classmethod
    def update_version_file(cls, file_path: Optional[Path] = None) -> tuple[bool, Self, Path]:
        '''
        Update the version file with the current version information.
        '''
        file_path = file_path or VERSION_FILE
        current_version = cls()
        if file_path.exists():
            file_version = cls.from_version_file(file_path=file_path)
            if file_version.commit == current_version.commit:
                logger.info(f"Version file {file_path} is up to date.")
                return False, file_version, file_path
        logger.info(f"Updating version file {file_path}.")
        return True, current_version, current_version.write_version_file(file_path=file_path)
    
    @classmethod
    def get_latest(cls) -> Self:
        '''
        Get the latest version information (and update the version file).
        '''
        _, version_info, _ = cls.update_version_file()
        return version_info


if __name__ == '__main__':
    print(f'Package Name: {PACKAGE_NAME}')
    print(f'Package Path: {PACKAGE_PATH}')
    print(f'Version: {VERSION}')
    if VERSION_FILE.exists():
        print(f'Version File: {VERSION_FILE}')
        VersionInfo.update_version_file(file_path=VERSION_FILE)
        updated, vi, fp = VersionInfo.update_version_file(file_path=VERSION_FILE)
        if updated:
            print(f'Updated Version File: {fp}')
        else:
            print(f'Version File is up to date: {fp}')
    else:
        vi = VersionInfo()
    print(vi)
    