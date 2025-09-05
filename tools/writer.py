from math import e
import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO, Generator, Callable, Mapping
from datetime import datetime, timezone
import re
from enum import Enum, StrEnum
import logging
from contextlib import contextmanager
import inspect
from dataclasses import dataclass

import pandas as pd

import statscan.enums.auto

logger = logging.getLogger(__name__)

AUTO_ENUMS_PATH = Path(statscan.enums.auto.__file__).parent


def to_dot_path(module_path: Path) -> str:
    # find the relative import path via sys.path
    for p in sys.path[1:]:
        try:
            relative_path = module_path.relative_to(p)
            return str(relative_path).replace('/', '.').replace('.py', '')
        except ValueError:
            continue
    raise ValueError(f"Module path {module_path} is not within any sys.path directories")


def cleanstr(s: str) -> str:
    """
    Clean a string by removing leading/trailing whitespace and converting to uppercase.
    """
    if s is None:
        return ""
    
    s_new = s
    try:
        for char in (' ', '-', '=', '/', '.'): # Replace certain characters underscores
            s_new = s_new.replace(char, '_')

        for char in ("'", '"'):  # Remove other characters altogether
            s_new = s_new.replace(char, '')

        # also convert super/subcript to normal (e.g. ² -> 2)
        s_new = s_new.translate(str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉', '01234567890123456789'))

        s_new = re.sub(r'[^\w_]+', '', s_new)  # Remove any characters that are not alphanumeric or underscore
        s_new = re.sub(r'_+', '_', s_new)  # Replace multiple underscores with a single underscore
        s_new = s_new.strip('_')  # Remove leading or trailing underscores that might have been created
        if s_new and s_new[0].isdigit():  # Ensure the name does not start with a digit
            s_new = '_' + s_new
    except Exception as e:
        logger.error(f"Error cleaning string '{s}': {e}")
    return s_new


def get_module_path(cls: type) -> Path:
    """
    Get the module path for a given class.
    """
    module_name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)).lower()
    return AUTO_ENUMS_PATH / f'{module_name}.py'


def write_method(
    f: TextIO, 
    method: Callable, 
    indent: int = 4,
) -> None:
    """
    Write a method to the file.
    """
    if isinstance(method, property):
        write_method(f, method.fget, indent=indent)
        if method.fset:
            write_method(f, method.fset, indent=indent)  #, prefix='@property\n@' + prefix if prefix else '@property')
        if method.fdel:
            write_method(f, method.fdel, indent=indent)
    else:
        f.write('\n')
        lines, _ = inspect.getsourcelines(method)
        m_indent = len(lines[0]) - len(lines[0].lstrip())
        for line in lines:
            f.write(' ' * indent + line[m_indent:])


@dataclass
class EnumEntry:
    key: str
    value: int
    comment: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.key, str):
            raise TypeError(f"key must be str, got {type(self.key).__name__}")
        if not isinstance(self.value, int):
            raise TypeError(f"value must be int, got {type(self.value).__name__}")
        if self.comment is not None and not isinstance(self.comment, str):
            raise TypeError(f"comment must be str or None, got {type(self.comment).__name__}")

    # def to_string(self, uppercase: bool = True, prefix: str = '',suffix: str = '') -> str:
    #     clean_key = cleanstr(prefix+self.key+suffix)
    #     if uppercase:
    #         clean_key = clean_key.upper()
    #     entry_str = f'{clean_key} = {self.value}'
    #     key_updated = (clean_key != self.key)
    #     if key_updated or self.comment:
    #         entry_str += '  #' + (f' ({self.key})' if key_updated else '') + (f' {self.comment}' if self.comment else '')
    #     return entry_str

    def clean_key(self, uppercase: bool = True, prefix: str = '', suffix: str = '') -> str:
        clean_key = cleanstr(prefix+self.key+suffix)
        if uppercase:
            clean_key = clean_key.upper()
        return clean_key

    def write_entry(
        self, 
        f: TextIO, 
        indent: int = 4, 
        uppercase: bool = True, 
        prefix: str = '', 
        suffix: str = ''
    ) -> str:
        """
        writes the enum entry to a file in the proper format, returns the generated key
        """
        clean_key = self.clean_key(uppercase=uppercase, prefix=prefix, suffix=suffix)
        entry_str = f'{clean_key} = {self.value}'
        key_updated = (clean_key != self.key)
        
        # Only show auto key if key was updated AND comment doesn't already start with parentheses
        auto_key_needed = key_updated and not (self.comment and self.comment.strip().startswith('('))
        
        if auto_key_needed or self.comment:
            entry_str += '  #' + (f' ({self.key})' if auto_key_needed else '') + (f' {self.comment}' if self.comment else '')

        f.write(' ' * indent + entry_str + '\n')
        return clean_key


def write_enum_class(
    f: TextIO, 
    entries: Iterable[EnumEntry],
    cls_template: Optional[type[Enum]] = None,
    cls_name: Optional[str] = None,
    cls_bases: Optional[tuple[type, ...]] = None,
    skip_methods: bool = False,
    skip_auto: bool = True,
):
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
    indent = 4

    f.write('\n\n')
    f.write(f'class {cls_name}({", ".join(b.__name__ for b in cls_bases)}):\n')
    f.write(' ' * indent +'"""\n')
    f.write(' ' * indent +f'Automatically generated Enum for {cls_name}\n')
    f.write(' ' * indent +'"""\n')

    written_keys = set()
    
    for e in entries:
        suffix = ''
        idx = 0
        
        while (e.clean_key(suffix=suffix)) in written_keys:
            idx += 1
            suffix = f'_{idx}'
        
        if suffix:
            logger.warning(f'Key {e.key} is duplicated in {cls_name}, renaming to {e.key}{suffix}.')
        else:
            logger.debug(f'key: {e.key} is unique')

        clean_key = e.write_entry(f=f, indent=indent, suffix=suffix)

        written_keys.add(clean_key)

    logger.info(f'wrote the following enum key names: {written_keys}')


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
                write_method(
                    f=f, 
                    method=v, 
                    indent=indent, 
                )
        logger.debug(f'...wrote class {cls_template.__name__}')


@contextmanager
def enum_file(
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


# def write_module(
#     df: pd.DataFrame,
#     cls_templates: dict[type[Enum], list[EnumEntry]],
#     module_path: Optional[Path] = None,
#     imports: Optional[dict[str, Optional[str | set[str]]]] = None,
#     overwrite: bool = False,
# ) -> None:
#     """
#     Write the GeoCode class definition to the file.
#     """
#     if imports is None:
#         imports = {}
#     if module_path is None:
#         first_cls = next(iter(cls_templates.keys()))
#         module_path = get_module_path(first_cls)
#     for t in cls_templates:
#         for b in t.__bases__:
#             if not b.__module__ in imports:
#                 imports[b.__module__] = set()
#             if isinstance(mod_imports := imports[b.__module__], set):
#                 mod_imports.add(b.__name__)
#             elif isinstance(mod_imports, str):
#                 mod_imports = {mod_imports, b.__name__}
#             else:
#                 raise TypeError(f"Expected set for imports[{b.__module__}], got {type(imports[b.__module__])}")
#             imports[b.__module__] = mod_imports

#     with enum_file(
#         fp=module_path,
#         imports=imports,
#         overwrite=overwrite,
#     ) as f:
#         for cls, entries in cls_templates.items():
#             write_enum_class(
#                 f=f, 
#                 cls_template=cls,
#                 entries=entries
#             )

# def update_imports_dict(
#     obj: type | Callable,
#     imports: Optional[dict[str, Optional[str | set[str]]]] = None,
# ) -> dict[str, Optional[str | set[str]]]:
#     """
#     Update the imports dictionary with a module and its items.
#     """
#     imports = imports or {}
#     try:
#         obj_mod: str = obj.__module__
#         obj_name: str = obj.__name__
#     except AttributeError as e:
#         raise ValueError(f"Object {obj} does not have a __module__ or __name__ attribute. Ensure it is a class or function.") from e

#     if isinstance(mod_imports := imports.get(obj_mod, set()), str):
#         mod_imports = {mod_imports}
#     elif mod_imports is None:
#         raise ValueError(f'Module {obj_mod} has already been defined in the imports dict with "None", cannot append {obj_name} to import mapping.')
#     mod_imports.add(obj_name)
#     imports[obj_mod] = mod_imports
#     return imports