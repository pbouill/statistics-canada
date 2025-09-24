# This file provides basic mappings for the build process
import os
from typing import Optional, Self, ClassVar, Any, Union, get_args, get_origin
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, fields, asdict, Field
from enum import StrEnum, auto
import logging

import statscan as base_pkg


_GIT_DIR_NAME: str = '.git'

PACKAGE_NAME: str = base_pkg.__name__
PACKAGE_PATH: Path = Path(base_pkg.__file__).parent
VERSION: Optional[str] = base_pkg.__version__
VERSION_FILE: Path = PACKAGE_PATH / '_version.py'

logger  = logging.getLogger(name=__name__)


class GitHubActionEnvVars(StrEnum):
    '''
    Environment variables used in GitHub Actions.
    '''

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> str:
        return name.upper()

    GITHUB_REPOSITORY = auto()  # The owner and repository name. For example, octocat/Hello-World.
    GITHUB_SHA = auto()  # The commit SHA that triggered the workflow.
    GITHUB_REF = auto()  # The branch or tag ref that triggered the workflow.
    GITHUB_WORKFLOW = auto()  # The name of the workflow.
    GITHUB_ACTOR = auto()  # The name of the person or app that initiated the workflow.
    GITHUB_WORKSPACE = auto()  # The GitHub workspace directory path.

    @property
    def env_value(self) -> Optional[str]:
        '''
        Get the value of the environment variable.
        Returns:
            str: The value of the environment variable.
        '''
        return os.getenv(self.value)


def print_dir_contents(path: Path, level: int = 0, max_level: int = 1) -> None:
    '''
    Print the contents of a directory.
    Args:
        path (Path): The path to the directory.
        level (int): The current level of recursion.
    '''
    print(f'{"  " * level}{path}/')
    for item in path.iterdir():
        if item.is_dir():
            if level >= max_level:
                print(f'{"  " * (level + 1)}- {item.name}/ (max level reached)')
                continue
            else:
                print_dir_contents(item, level + 1, max_level)
                continue
        else:
            print(f'{"  " * (level + 1)}- {item.name} ({item.stat().st_size} bytes)')
            continue

def get_head_ref_path(git_path: Optional[Path] = None) -> Path:
    '''
    Get the current git HEAD reference.
    Args:
        git_path (Path): The path to the git repository. If None, uses the current directory.
    Returns:
        str: The current git HEAD reference.
    '''
    git_path = git_path or (PACKAGE_PATH.parent / _GIT_DIR_NAME)
    head_path = git_path / 'HEAD'
    
    if not head_path.exists():
        raise FileNotFoundError(f'HEAD file path "{head_path.resolve()}" not found. Please ensure you are in a valid git repository.')

    ref: Optional[str] = None
    with head_path.open() as f:
        for l in f.readlines():
            if l.startswith('ref:'):
                # Extract the reference path from the line
                ref = l.split(':', 1)[1].strip()
                break
    if ref is None:
        raise ValueError(f'No reference found in HEAD file at {head_path.resolve()}.')
    
    ref_path = git_path / ref
    if not ref_path.exists():
        raise FileNotFoundError(f'Reference file "{ref_path.resolve()}" not found. Please ensure the reference exists in the git repository.')

    return ref_path

def get_commit_hash(repo_path: Optional[Path] = None) -> str:
    '''
    Get the current git commit hash.
    Args:
        repo_dir (Path): The path to the git repository. If None, uses the current directory.
    Returns:
        str: The current git commit hash.
    '''
    repo_path = repo_path or PACKAGE_PATH.parent
    git_path = repo_path / _GIT_DIR_NAME

    if not git_path.exists():
        raise FileNotFoundError(f"Git repository not found in {git_path.resolve()}. Please ensure you are in a valid git repository.")
    
    git_ref_path = get_head_ref_path(git_path=git_path)

    with git_ref_path.open() as f:
        return f.read().strip()

@dataclass
class VersionInfo:
    SUPPORTED_TYPES: ClassVar = (int, float, str, bool)
    package_name: str = PACKAGE_NAME
    build_time: Optional[datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    commit: Optional[str] = field(default_factory=lambda: GitHubActionEnvVars.GITHUB_SHA.env_value or get_commit_hash())

    @property  # type: ignore[no-redef]
    def version(self) -> Optional[str]:
        return self.version_str_from_datetime(dt=self.build_time) if self.build_time else None

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

        cls_fields: dict[str, Field] = {f.name: f for f in fields(cls)}

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
                    
                key = key.strip()

                if key.startswith('__') and key.endswith('__'):
                    key = key[2:-2]
                    
                if (fld := cls_fields.get(key, None)) is not None:
                    value: Any
                    value_str = value_str.split("#")[0].strip().replace("'", "").replace('"', "")
                    
                    # check if the field type is a union
                    if get_origin(fld.type) is Union:
                        # If it's a Union, we need to check the types inside it
                        fld_types = get_args(fld.type)
                    else:
                        fld_types = (fld.type,)
                    if v_type is not None:
                        if v_type in cls.SUPPORTED_TYPES:
                            if v_type is bool:
                                if value_str.lower() in ('true', '1'):
                                    value = True
                                elif value_str.lower() in ('false', '0'):
                                    value = False
                                else:
                                    raise ValueError(f"Invalid boolean value for key {key}: {value_str}")
                            else:
                                value = v_type(value_str)
                        else:
                            raise TypeError(f"Unsupported type {v_type} for key {key}. Supported types are: {cls.SUPPORTED_TYPES}")
                    
                    if v_type in fld_types:
                        kwargs[key] = value
                        continue
                    elif (datetime in fld_types) and isinstance(value, str):
                        kwargs[key] = datetime.fromisoformat(value)
                        continue
        return cls(package_name=file_path.parent.name, **kwargs)

    
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
                v = getattr(self, fld.name)
                if isinstance(v, datetime):
                    v = v.isoformat()
                if isinstance(v, self.SUPPORTED_TYPES):
                    f.write(f"__{fld.name}__: {type(v).__name__} = '{str(v)}'\n")
                else:
                    f.write(f' # {fld.name}: {fld.type} = {v}\n')
        return file_path
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

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
        updated, vi, fp = VersionInfo.update_version_file(file_path=VERSION_FILE)
        if updated:
            print(f'Updated Version File: {fp}')
        else:
            print(f'Version File is up to date: {fp}')
    else:
        print(f'Version File does not exist: {VERSION_FILE}. Creating new version file.')
        vi = VersionInfo()
        vi.write_version_file()
    print(vi)
    