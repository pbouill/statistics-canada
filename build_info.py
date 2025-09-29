# This file provides basic mappings for the build process
import os
import sys
from typing import Optional, Self, ClassVar, Any, Union, get_args, get_origin
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, fields, asdict, Field
from enum import StrEnum, auto
import json
import logging
import tomllib


logger = logging.getLogger(name=__name__)

_GIT_DIR_NAME: str = ".git"
_PYPROJECT_FILE_NAME: str = "pyproject.toml"
DEFAULT_VERSION_FILE_NAME: str = "_version.py"
DEFAULT_REPOSITORY_PATH: Path = Path.cwd()


class GitHubActionEnvVars(StrEnum):
    """
    Environment variables used in GitHub Actions.
    """

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> str:
        return name.upper()

    GITHUB_REPOSITORY = (
        auto()
    )  # The owner and repository name. For example, octocat/Hello-World.
    GITHUB_SHA = auto()  # The commit SHA that triggered the workflow.
    GITHUB_REF = auto()  # The branch or tag ref that triggered the workflow.
    GITHUB_WORKFLOW = auto()  # The name of the workflow.
    GITHUB_ACTOR = auto()  # The name of the person or app that initiated the workflow.
    GITHUB_WORKSPACE = auto()  # The GitHub workspace directory path.

    @property
    def env_value(self) -> Optional[str]:
        """
        Get the value of the environment variable.
        Returns:
            str: The value of the environment variable.
        """
        return os.getenv(self.value)


def print_dir_contents(path: Path, level: int = 0, max_level: int = 1) -> None:
    """
    Print the contents of a directory.
    Args:
        path (Path): The path to the directory.
        level (int): The current level of recursion.
    """
    print(f"{'  ' * level}{path}/")
    for item in path.iterdir():
        if item.is_dir():
            if level >= max_level:
                print(f"{'  ' * (level + 1)}- {item.name}/ (max level reached)")
                continue
            else:
                print_dir_contents(item, level + 1, max_level)
                continue
        else:
            print(f"{'  ' * (level + 1)}- {item.name} ({item.stat().st_size} bytes)")
            continue


def get_head_ref_path(git_path: Path) -> Path:
    """
    Get the current git HEAD reference.
    Args:
        git_path (Path): The path to the git repository.
    Returns:
        str: The current git HEAD reference.
    """
    # git_path default is repo root .git directory; try repo_dir or cwd
    head_path = git_path / "HEAD"

    if not head_path.exists():
        raise FileNotFoundError(
            f'HEAD file path "{head_path.resolve()}" not found. Please ensure you are in a valid git repository.'
        )

    ref: Optional[str] = None
    with head_path.open() as f:
        for line in f.readlines():
            if line.startswith("ref:"):
                # Extract the reference path from the line
                ref = line.split(":", 1)[1].strip()
                break
    if ref is None:
        raise ValueError(f"No reference found in HEAD file at {head_path.resolve()}.")

    ref_path = git_path / ref
    if not ref_path.exists():
        raise FileNotFoundError(
            f'Reference file "{ref_path.resolve()}" not found. Please ensure the reference exists in the git repository.'
        )

    return ref_path


def get_commit_hash(repo_path: Optional[Path] = None) -> tuple[str, str]:
    """
    Get the current git commit hash.
    Args:
        repo_dir (Path): The path to the git repository. If None, uses the current directory.
    Returns:
        tuple[str, str]: The current git branch name and commit hash.
    """
    repo_path = repo_path or Path.cwd()
    git_path = repo_path / _GIT_DIR_NAME

    if not git_path.exists():
        raise FileNotFoundError(
            f"Git repository not found in {git_path.resolve()}. Please ensure you are in a valid git repository."
        )

    git_ref_path = get_head_ref_path(git_path=git_path)

    with git_ref_path.open() as f:
        commit = f.read().strip()
    
    ref = git_ref_path.relative_to(git_path / 'refs/heads/')
    return str(ref), commit


def get_utc_timestamp() -> datetime:
    """Get the current UTC timestamp."""
    return datetime.now(tz=timezone.utc)

def get_version_str(dt: Optional[datetime]) -> str:
    """Create or convert a datetime to a version string of the form YYYY.M.D.HHMMSS."""
    dt = dt or get_utc_timestamp()
    return f"{dt.year}.{dt.month}.{dt.day}.{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"

def version_str_to_datetime(version: str) -> datetime:

    year, month, day, time_part = version.split(".")
    hour = int(time_part[0:2])
    minute = int(time_part[2:4])
    second = int(time_part[4:6])
    return datetime(
        year=int(year),
        month=int(month),
        day=int(day),
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=timezone.utc
    )

def get_pyproject(repo_path: Path) -> dict[str, Any]:
    """
    Load and parse the pyproject.toml file from the given path.
    Args:
        path (Path): The path to the directory containing pyproject.toml.
    Returns:
        dict: The parsed pyproject.toml content.
    """
    pyproject_path = repo_path / _PYPROJECT_FILE_NAME
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path.resolve()}")
    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


class BuildInfoEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


@dataclass
class BuildInfo:
    SUPPORTED_TYPES: ClassVar = (int, float, str, bool)
    repo_path: Path
    build_time: datetime = field(
        default_factory=get_utc_timestamp
    )
    commit: Optional[str] = None
    branch: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.repo_path, Path):
            self.repo_path = Path(self.repo_path)
        if None in (self.commit, self.branch):
            commit = GitHubActionEnvVars.GITHUB_SHA.env_value
            branch = GitHubActionEnvVars.GITHUB_REF.env_value
            if all([commit, branch]):
                logger.info("Using GitHub Actions environment variables for commit and branch")
                self.commit = commit
                self.branch = branch
            else:
                logger.info("Retrieving commit and branch from git repository")
                self.branch, self.commit = get_commit_hash(repo_path=self.repo_path)

    @property  # type: ignore[no-redef]
    def version(self) -> Optional[str]:
        if self.build_time:
            return get_version_str(dt=self.build_time)
        else:
            return None

    def update_commit_hash_from_repo(self):
        self.commit = get_commit_hash(repo_path=self.repo_path)

    @classmethod
    def from_version_file(cls, file_path: Path) -> Self:
        """
        Load version information from a file.
        Raises ValueError if any required fields are missing from the file.
        """
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
                        raise ValueError(
                            f"Cannot parse key: {key_type[0]}. {key_type=}"
                        )
                    for t in cls.SUPPORTED_TYPES:
                        if key_type[1].strip() == t.__name__:
                            v_type = t
                            break
                    key = key_type[0]

                key = key.strip()

                if key.startswith("__") and key.endswith("__"):
                    key = key[2:-2]

                if (fld := cls_fields.get(key, None)) is not None:
                    value: Any
                    value_str = (
                        value_str.split("#")[0]
                        .strip()
                        .replace("'", "")
                        .replace('"', "")
                    )

                    # check if the field type is a union
                    if get_origin(fld.type) is Union:
                        # If it's a Union, we need to check the types inside it
                        fld_types = get_args(fld.type)
                    else:
                        fld_types = (fld.type,)
                    if v_type is not None:
                        if v_type in cls.SUPPORTED_TYPES:
                            if v_type is bool:
                                if value_str.lower() in ("true", "1"):
                                    value = True
                                elif value_str.lower() in ("false", "0"):
                                    value = False
                                else:
                                    raise ValueError(
                                        f"Invalid boolean value for key {key}: {value_str}"
                                    )
                            else:
                                value = v_type(value_str)
                        else:
                            raise TypeError(
                                f"Unsupported type {v_type} for key {key}. Supported types are: {cls.SUPPORTED_TYPES}"
                            )

                    if v_type in fld_types:
                        kwargs[key] = value
                        continue
                    elif (datetime in fld_types) and isinstance(value, str):
                        kwargs[key] = datetime.fromisoformat(value)
                        continue
        return cls(repo_path=file_path.parent, **kwargs)

    def write_version_file(self, version_file: Optional[Path] = None) -> Path:
        """
        Write the version number and build metadata to a file.
        """
        version_file = version_file or (self.repo_path / DEFAULT_VERSION_FILE_NAME)
        with open(file=version_file, mode="w") as f:
            f.write(f"# This file is automatically generated by ../{Path(__file__).name} \n")
            f.write(f"__version__: str = '{self.version}'\n")
            for fld in fields(self):
                if fld.name == "repo_path":
                    continue  # repo_path is derived from the version file path
                v = getattr(self, fld.name)
                if isinstance(v, datetime):
                    v = v.isoformat()
                if isinstance(v, self.SUPPORTED_TYPES):
                    f.write(f"__{fld.name}__: {type(v).__name__} = '{str(v)}'\n")
                else:
                    f.write(f" # {fld.name}: {fld.type} = {v}\n")
        return version_file

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # add props to dict
        for k, v in self.__class__.__dict__.items():
            if isinstance(v, property):
                d[k] = getattr(self, k)
        return d

    def to_json(self) -> str:
        d = self.to_dict()
        return json.dumps(d, indent=2, skipkeys=True, cls=BuildInfoEncoder)

    def update_version_file(self, version_file: Path) -> bool:
        """
        Update the version file with the current version information.
        If the commit hash matches the existing file, no update is performed.

        Returns:
            bool: True if the file was updated, False if no update was needed.
        """
        bi = self.from_version_file(file_path=version_file) if version_file.exists() else None

        if bi:
            if self.commit == bi.commit:
                logger.info(f"Version file {version_file} is up to date.")
                return False
            else:
                logger.info(f"Updating version file {version_file}.")
        else:
            logger.info(
                f"Version file {version_file} does not exist. Creating new version file."
            )
        self.write_version_file(version_file=version_file)
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="build_info utilities: generate version strings and read/write _version.py"
    )

    def raise_log_parser_error(msg: str) -> None:
        logger.error(msg)
        parser.error(msg)
        raise SystemExit(2)

    parser.add_argument(
        "-l",
        "--log-level",
        help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL or corresponding integer values).",
    )
    func_group = parser.add_mutually_exclusive_group()
    func_group.add_argument(
        "-s",
        "--version-string",
        action="store_true",
        help="Generate a new version string based on the current UTC datetime."
    )
    func_group.add_argument(
        "-n",
        "--new",
        action="store_true",
        help="Create a new version file.",
    )
    func_group.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update the version file with the current version information.",
    )
    func_group.add_argument(
        "-r",
        "--read",
        action="store_true",
        help="Read and display the current version information from the version file.",
    )

    create_group = parser.add_argument_group(
        title="Create/Update Version File",
        description="Options for creating or updating the version file."
    )
    create_group.add_argument(
        "-c",
        "--commit",
        type=str,
        help="The commit hash to include in the version file.",
    )
    create_group.add_argument(
        "-t",
        "--build-time",
        type=datetime.fromisoformat,
        help="The build time (iso-8601 format) to include in the version file.",
    )
    create_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a trial run with no changes made."
    )

    gen_grp = parser.add_argument_group(
        title='Read/Create/Update Version File',
        description='Common options for specifying package and version file paths.'
    )

    # pkg_path_grp = parser.add_mutually_exclusive_group(required=False)
    gen_grp.add_argument(
        "repo_path",
        nargs="?",
        type=Path,
        default=DEFAULT_REPOSITORY_PATH,
        help="Repository path (default: . ).",
    )

    gen_grp.add_argument(
        "-f",
        "--version-file",
        dest="version_file",
        type=str,
        default=DEFAULT_VERSION_FILE_NAME,
        help=f"Version file name (default: {DEFAULT_VERSION_FILE_NAME}).",
    )
    gen_grp.add_argument(
        "-p",
        "--property",
        type=str,
        choices=[
            'version',
            'commit',
            'branch',
            'build_time'
        ],
        help="Only the specified property will be returned, otherwise the full JSON object is returned.",
    )

    args = parser.parse_args()
    if args.log_level:
        try:
            args.log_level = int(args.log_level)
        except ValueError:
            pass
        logging.basicConfig(level=args.log_level)

    logger.debug(f"args: {args}")

    if not any(
        [
            args.version_string,
            args.update,
            args.read,
        ]
    ):
        logger.debug("No action specified, defaulting to reading current version file.")
        args.read = True

    if args.version_string:  # quick exit if all we need is a new version string
        print(get_version_str(args.build_time))
        sys.exit(0)

    else:
        repo_path: Path = args.repo_path
        if not repo_path.exists() or not repo_path.is_dir():
            raise_log_parser_error(f"Invalid repository path: {repo_path}")
        logger.debug(f"Using repository path: {repo_path}")

        version_file: Path = repo_path / args.version_file
        logger.info(f"Using version file path: {version_file}")

        if args.new:
            kwargs = {}
            if args.build_time:
                kwargs['build_time'] = args.build_time
            if args.commit:
                kwargs['commit'] = args.commit
            bi = BuildInfo(
                repo_path=repo_path, 
                **kwargs
            )
            if args.dry_run:
                logger.info(f"Dry run: would create new version file at: {version_file}")
            else:
                fp = bi.write_version_file(version_file=version_file)
                logger.info(f"Created new version file at: {fp}")
        else:
            bi = BuildInfo.from_version_file(file_path=version_file)

        if args.update:
            if args.commit:
                bi.commit = args.commit
            if args.build_time:
                bi.build_time = args.build_time
            if args.dry_run:
                logger.info(f"Dry run: would update version file at: {version_file}")
            else:
                if bi.update_version_file(version_file=version_file):
                    logger.info(f"Updated version file at: {version_file}")
                else:
                    logger.info(f"No update needed for version file at: {version_file}")

        if args.property:
            print(str(getattr(bi, args.property)))
        else:
            print(bi.to_json())

        sys.exit(0)
