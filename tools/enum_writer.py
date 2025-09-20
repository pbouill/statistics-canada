import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Iterable, 
    Optional, 
    TextIO, 
    Generator, 
    Callable, 
    Mapping, 
    Sequence,
    Any,
)
from datetime import datetime, timezone
import re
from enum import Enum
import logging
from contextlib import contextmanager
import inspect

import unicodedata

import statscan.enums.auto
from tools.substitution import SubstitutionEngine

logger = logging.getLogger(__name__)

AUTO_ENUMS_PATH = Path(statscan.enums.auto.__file__).parent


class InvalidEnumNameError(ValueError):
    pass


class InvalidEnumValueError(ValueError):
    pass


class InvalidEnumCommentError(ValueError):
    pass


class EnumEntry:
    """
    A dataclass representing a single entry in an enum.

    Note: this class is not responsible for checking uniqueness of enum keys
    """
    def __init__(self, name: str, value: int, comment: Optional[str] = None):
        # Clean and validate inputs before assignment
        if isinstance(comment, str) and "\n" in comment:
            # Clean newlines and other problematic characters from comments
            comment = re.sub(r'\s+', ' ', comment.strip())
            if not comment:
                comment = None
        
        self.name = name
        self.value = value
        self.comment = comment

    @staticmethod
    def validate_name(name: str, check_case: bool = True) -> None:
        if not isinstance(name, str):
            raise InvalidEnumNameError(f"Enum name must be a {str}, got {type(name)}")
        if not name:
            raise InvalidEnumNameError("Enum name cannot be empty")
        if name[0].isdigit():
            raise InvalidEnumNameError(f"Enum name cannot start with a digit: {name}")
        if not (match := re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name)):
            raise InvalidEnumNameError(f"Enum name contains invalid characters: {name} ({match})")
        if check_case and not name.isupper():
            raise InvalidEnumNameError(f"Enum name must be uppercase: {name}")

    @staticmethod
    def validate_value(value: int) -> None:
        if not isinstance(value, int):
            raise InvalidEnumValueError(f"Enum value must be an {int}, got {type(value)}")

    @staticmethod
    def validate_comment(comment: Optional[str]) -> None:
        if comment is not None and not isinstance(comment, str):
            raise InvalidEnumCommentError(f"Enum comment must be a {str} or None, got {type(comment)}")
        elif isinstance(comment, str) and "\n" in comment:
            # Clean newlines and other problematic characters from comments
            comment = re.sub(r'\s+', ' ', comment.strip())
            if not comment:
                comment = None

    @staticmethod
    def clean_name(s: str, upper_case: bool = True) -> str:
        """
        Clean an enum name by replacing or removing invalid characters.
        """
        if not isinstance(s, str):
            raise TypeError(f"Expected {str}, got {type(s)}")
        if not s:
            raise ValueError("Cannot clean empty string")

        s_new = s
        try:
            # Replace certain characters with underscores
            replace_with_underscore = {
                " ",
                "-",
                "=",
                "/",
                ".",
                "~",
            }
            s_new = SubstitutionEngine.sub_chars(s_new, sub_chars=replace_with_underscore, replacement="_")

            # Remove quotes
            s_new = SubstitutionEngine.sub_chars(s_new, sub_chars={"'", '"'}, replacement="")

            # also convert super/subcript to normal (e.g. ² -> 2)
            s_new = s_new.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉", "01234567890123456789"))

            # Handle Unicode characters - normalize and convert to ASCII equivalent
            s_new = unicodedata.normalize('NFD', s_new)
            s_new = ''.join(c for c in s_new if unicodedata.category(c) != 'Mn')
            
            # Remove any characters that are not alphanumeric or underscore
            s_new = re.sub(r"[^\w_]+", "", s_new)
            
            # Replace multiple underscores with a single underscore
            s_new = re.sub(r"_+", "_", s_new)

            # Remove leading or trailing underscores that might have been created
            s_new = s_new.strip("_")  
            if (s_new and s_new[0].isdigit()):  # Ensure the name does not start with a digit
                s_new = "_" + s_new

            if upper_case:
                s_new = s_new.upper()
        except Exception as e:
            logger.error(f"Error cleaning string '{s}': {e}")
        return s_new
    
    @staticmethod
    def prepare_name(
        s: str, 
        subs_engine: Optional[SubstitutionEngine] = None, 
        upper_case: bool = True
    ) -> str:
        s_new = s
        if subs_engine:
            s_new = subs_engine.substitute(s_new)
        try:
            s_new = EnumEntry.clean_name(s_new, upper_case=upper_case)
        except ValueError:
            # Handle empty strings or other ValueError cases from clean_name
            s_new = "UNKNOWN"
        return s_new


    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self.validate_name(value, check_case=False)
        self._name = value

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        if not isinstance(v, int):
            raise InvalidEnumValueError(f"Enum value must be an {int}, got {type(v)}")
        self._value = v

    @property
    def comment(self) -> Optional[str]:
        return self._comment

    @comment.setter
    def comment(self, c: Optional[str]):
        if c is not None and not isinstance(c, str):
            raise InvalidEnumCommentError(f"Enum comment must be a {str} or None, got {type(c)}")
        elif isinstance(c, str) and "\n" in c:
            raise InvalidEnumCommentError("Enum comment cannot contain newlines")
        self._comment = c

    def __str__(self) -> str:
        return f"{self.name} = {self.value}" + (
            f"  # {self.comment}" if self.comment else ""
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, value={self.value!r}, comment={self.comment!r})"


class AbstractEnumWriter(ABC):
    subs_engine: SubstitutionEngine = SubstitutionEngine()

    @abstractmethod
    def generate_enum_entries(self, data: Any, *args, **kwargs) -> Iterable[EnumEntry]:
        """
        Abstract method to generate enum entries.
        """
        pass

    @classmethod
    @contextmanager
    def enum_file(
        cls,
        fp: Path,
        imports: Mapping[str, Optional[str | Iterable[str]]],
        overwrite: bool = False,
    ) -> Generator[TextIO, None, None]:
        """
        Context manager to write an enum file.
        """
        fp.parent.mkdir(parents=True, exist_ok=True)
        if not overwrite and fp.exists():
            raise FileExistsError(f"Module already exists at {fp}. Use 'overwrite=True' to regenerate.")
        try:
            with fp.open(mode='w') as f:
                f.write(f'# !! This file is automatically generated by: {Path(__file__).name}\n')
                f.write(f'#     date: {datetime.now(tz=timezone.utc).isoformat()}\n\n')
                for import_module, import_items in imports.items():
                    if import_items:
                        if isinstance(import_items, str):
                            import_items = [import_items]
                        f.write(f'from {import_module} import {", ".join(import_items)}\n')
                yield f
        finally:
            logger.info(f"Enum file written to {fp}")

    @classmethod
    def validate_enum_entries(
        cls,
        entries: Sequence[EnumEntry], 
        check_case: bool = True,
    ) -> None:
        """
        Validate the enum entries for uniqueness and correctness.
        """
        duplicate_names = cls.get_duplicate_names(entries)
        if duplicate_names:
            raise InvalidEnumNameError(f"Duplicate enum names found: {duplicate_names.values()}")

        duplicate_values = cls.get_duplicate_values(entries)
        if duplicate_values:
            raise InvalidEnumValueError(f"Duplicate enum values found: {duplicate_values.values()}")

        if check_case:
            invalid_names = [e.name for e in entries if not e.name.isupper()]
            if invalid_names:
                raise InvalidEnumNameError(f"Enum names must be uppercase: {invalid_names}")

    @classmethod
    def get_duplicate_names(cls, entries: Sequence[EnumEntry]) -> dict[int, EnumEntry]:
        """
        Get a dictionary of duplicate entries (name) where the key is the index of the  
        entry in the provided list.
        """
        names: set[str] = set()
        duplicate_entries: dict[int, EnumEntry] = {}
        for i, entry in enumerate(entries):
            if entry.name in names:
                duplicate_entries[i] = entry
            names.add(entry.name)
        return duplicate_entries

    @classmethod
    def get_duplicate_values(cls, entries: Iterable[EnumEntry]) -> dict[int, EnumEntry]:
        """
        Get a dictionary of duplicate entries (value) where the key is the index of the
        entry in the provided list
        """
        values: set[int] = set()
        duplicate_entries: dict[int, EnumEntry] = {}
        for i, entry in enumerate(entries):
            if entry.value in values:
                duplicate_entries[i] = entry
            values.add(entry.value)
        return duplicate_entries

    @classmethod
    def write_enum_entry(
        cls,
        f: TextIO,
        entry: EnumEntry,
        indent: int = 0,
    ) -> None:
        """
        Write a single enum entry to the file.
        """
        f.write(' ' * indent + str(entry) + '\n')

    @classmethod
    def write_method(
        cls,
        f: TextIO,
        method: Callable,
        indent: int = 0,
    ) -> None:
        """
        Write a method to the file.
        """
        if isinstance(method, property):
            cls.write_method(f, method.fget, indent=indent)
            if method.fset:
                cls.write_method(
                    f, method.fset, indent=indent
                )  # , prefix='@property\n@' + prefix if prefix else '@property')
            if method.fdel:
                cls.write_method(f, method.fdel, indent=indent)
        else:
            f.write("\n")
            lines, _ = inspect.getsourcelines(method)
            m_indent = len(lines[0]) - len(lines[0].lstrip())
            for line in lines:
                f.write(" " * indent + line[m_indent:])

    @classmethod
    def write_class(
        cls,
        f: TextIO, 
        entries: Iterable[EnumEntry],
        cls_template: Optional[type[Enum]] = None,
        cls_name: Optional[str] = None,
        cls_bases: Optional[tuple[type, ...]] = None,
        skip_methods: bool = False,
        skip_auto: bool = True,
        indent: int = 0,
    ) -> None:
        """
        Write the enum class definition to the file.
        """
        if not cls_template:
            if not cls_name:
                raise ValueError("Must provide either cls_template or cls_name")
            cls_bases = (Enum,)
        else:
            cls_name = cls_name or cls_template.__name__
            cls_bases = cls_bases or cls_template.__bases__

        logger.debug(f'Writing class {cls_name} to file from template {cls_template}...')
        # indent = 4

        f.write('\n\n')
        f.write(' ' * indent + f'class {cls_name}({", ".join(b.__name__ for b in cls_bases)}):\n')
        cls_indent = indent + 4
        f.write(' ' * cls_indent +'"""\n')
        f.write(' ' * cls_indent +f'Automatically generated Enum for {cls_name}\n')
        if cls_template and cls_template.__doc__:
            f.write(' ' * cls_indent +'\n')
            for line in cls_template.__doc__.splitlines():
                f.write(' ' * cls_indent +line.strip() + '\n')
        f.write(' ' * cls_indent +'"""\n')

        for e in entries:
            cls.write_enum_entry(f=f, entry=e, indent=cls_indent)

        f.write('\n')

        if cls_template:
            if not skip_methods:
                for k, v in cls_template.__dict__.items():  # write the methods and properties
                    if k.startswith('__') and k.endswith('__'):  # skip dunder methods
                        continue
                    if skip_auto and (k == '_generate_next_value_'):
                        continue
                    if inspect.isfunction(v):
                        logger.debug(f'[{cls_template.__name__}] found {type(v)} {k}.')
                    elif isinstance(v, (property, staticmethod, classmethod)):
                        logger.debug(f'[{cls_template.__name__}] found {type(v)} {k}.')
                    else:
                        continue
                    cls.write_method(
                        f=f, 
                        method=v, 
                        indent=cls_indent, 
                    )

        logger.debug(f'...wrote class {cls_name}')

    @staticmethod
    def to_dot_path(module_path: Path) -> str:
        # find the relative import path via sys.path
        for p in sys.path[1:]:
            try:
                relative_path = module_path.relative_to(p)
                return str(relative_path).replace("/", ".").replace(".py", "")
            except ValueError:
                continue
        raise ValueError(
            f"Module path {module_path} is not within any sys.path directories"
        )

    @classmethod
    def resolve_duplicate_names(
        cls, 
        entries: Sequence[EnumEntry],
        original_names: Sequence[str],
    ) -> None:
        """
        Resolve duplicate enum names by applying substitutions/removing truncation, and appending suffixes.
        """
        if (n_entries := len(entries)) != (n_original := len(original_names)):
            raise ValueError(f"Entries length {n_entries} does not match original names length {n_original}")

        if duplicates := cls.get_duplicate_names(entries):
            logger.warning(f"Resolving {len(duplicates)} duplicate enum names...")

            # first pass try removing truncation
            for idx, e in duplicates.items():
                
                orig_name = original_names[idx]
                name = cls.subs_engine.substitute(text=orig_name, truncate=False)
                try:
                    e.name = EnumEntry.clean_name(name)
                except ValueError as ve:
                    # Handle empty names with fallback
                    logger.warning(f"Empty name for original '{orig_name}' after removing truncation: {ve}")
                    e.name = 'UNKNOWN'

            # re-check for duplicates
            if duplicates := cls.get_duplicate_names(entries):
                # final pass, add suffixes if still duplicates
                logger.warning(
                    f"Handling {len(duplicates)} duplicate entries in final pass..."
                )
                dupe_names: dict[str, list[EnumEntry]] = {}
                for e in duplicates.values():
                    if e.name not in dupe_names:
                        dupe_names[e.name] = []
                    dupe_names[e.name].append(e)

                for same_name, same_name_entries in dupe_names.items():
                    logger.info(
                        f"Processing {len(same_name_entries)} entries with duplicate name: {same_name}"
                    )
                    # sort the list based on the value
                    same_name_entries.sort(key=lambda x: x.value)
                    for i, e in enumerate(same_name_entries, start=1):
                        if len(same_name_entries) > 100:
                            suffix = f"{i:03d}"
                        elif len(same_name_entries) > 10:
                            suffix = f"{i:02d}"
                        else:
                            suffix = f"{i}"
                        e.name = f"{e.name}_{suffix}"
            
            # we've done all we could... raise the error
            if duplicates := cls.get_duplicate_names(entries):
                raise InvalidEnumNameError(f'Duplicate enum names remain after resolution: {duplicates.values()}')
            
