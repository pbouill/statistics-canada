import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO, Generator, Callable, Mapping
from datetime import datetime, timezone
import re
from enum import Enum, StrEnum
import logging
from contextlib import contextmanager
import inspect

import pandas as pd

import statscan.enums.auto
from statscan.enums.schema import Schema, SACType
from statscan.enums.geocode.geocode import GeoCode, GeoAttributeColumn2021
from statscan.enums.geocode.pr_geocode import ProvinceGeoCode
from statscan.enums.geocode.cd_geocode import CensusDivisionGeoCode
from statscan.enums.geocode.cma_geocode import CensusMetropolitanAreaGeoCode
from statscan.url import GEO_ATTR_FILE_2021_URL
from statscan.util.get_data import download_data, unpack_to_dataframe

logger = logging.getLogger(__name__)

AUTO_ENUMS_PATH = Path(statscan.enums.auto.__file__).parent
KEY_COLUMN = "key_column"
SUFFIX_COLUMN = "suffix_column"
KEY_COUNT_COLUMN = "total_keys"

EnumMapSig = tuple[
    GeoAttributeColumn2021 | str,  # enum_name_col
    GeoAttributeColumn2021 | str,  # enum_value_col
    Optional[GeoAttributeColumn2021 | str],  # enum_desc_col
    Optional[GeoAttributeColumn2021 | str],  # name/key prefix
]


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


def cleanstr(s: str) -> str:
    """
    Clean a string by removing leading/trailing whitespace and converting to uppercase.
    """
    for char in (" ", "-"):  # Replace spaces, hyphens, and periods with underscores
        s = s.replace(char, "_")

    for char in ("'", '"', "."):  # Remove apostrophes, quotes, and periods
        s = s.replace(char, "")
    s = re.sub(
        r"[^\w_]+", "", s
    )  # Remove any characters that are not alphanumeric or underscore
    s = re.sub(r"_+", "_", s)  # Replace multiple underscores with a single underscore
    s = s.strip(
        "_"
    )  # Remove leading or trailing underscores that might have been created
    if s and s[0].isdigit():  # Ensure the name does not start with a digit
        s = "_" + s
    return s


def get_module_path(cls: type) -> Path:
    """
    Get the module path for a given class.
    """
    module_name = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1_\2",
        re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__),
    ).lower()
    return AUTO_ENUMS_PATH / f"{module_name}.py"


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
            write_method(
                f, method.fset, indent=indent
            )  # , prefix='@property\n@' + prefix if prefix else '@property')
        if method.fdel:
            write_method(f, method.fdel, indent=indent)
    else:
        f.write("\n")
        lines, _ = inspect.getsourcelines(method)
        m_indent = len(lines[0]) - len(lines[0].lstrip())
        for line in lines:
            f.write(" " * indent + line[m_indent:])


def write_enum_class(
    f: TextIO,
    cls_template: type[Enum],
    cls_name: Optional[str] = None,
    cls_bases: Optional[tuple[type, ...]] = None,
    df: Optional[pd.DataFrame] = None,
    mapping: Optional[EnumMapSig] = None,
    skip_methods: bool = False,
    skip_auto: bool = True,
):
    """
    Write the enum class definition to the file.
    """
    cls_name = cls_name or cls_template.__name__
    cls_bases = cls_bases or cls_template.__bases__

    logger.debug(f"Writing class {cls_name} to file from template {cls_template}...")
    indent = 4

    f.write("\n\n")
    f.write(f"class {cls_name}({', '.join(b.__name__ for b in cls_bases)}):\n")
    f.write(" " * indent + '"""\n')
    f.write(" " * indent + f"Automatically generated Enum for {cls_name}\n")
    if mapping is not None:
        name_col, val_col, desc_col, prefix_col = mapping

        f.write(" " * indent + f"Name: {name_col}\n")
        f.write(" " * indent + f"Value: {val_col}\n")
        if desc_col:
            f.write(" " * indent + f"Description: {desc_col}\n")
        if prefix_col:
            f.write(
                " " * indent
                + f"Prefix: {prefix_col if isinstance(prefix_col, Enum) else '(custom)'}\n"
            )

        # convert Enum columns to strings if they are Enums
        if isinstance(name_col, Enum):
            name_col = str(name_col.value)
        if isinstance(val_col, Enum):
            val_col = str(val_col.value)
        if isinstance(desc_col, Enum):
            desc_col = str(desc_col.value)
        if isinstance(prefix_col, Enum):
            prefix_col = str(prefix_col.value)
    f.write(" " * indent + '"""\n')

    # write any class attributes, use inspect to find them
    for k, v in inspect.get_annotations(cls_template).items():
        print(k, v, getattr(cls_template, k, None))
        vtype = str(v).split(".")[-1]
        print(f"[{cls_template.__name__}] {k} type: {vtype}")
        print(
            "" * indent + f"{k}: {type(v).__name__} = {getattr(cls_template, k, None)}"
        )

    if df is not None:
        if mapping is None:
            raise ValueError("Mapping must be provided if DataFrame is provided.")
        # drop duplicate values and sort by value (initially, the rows will be resorted by resolved "unique_name" later...)
        sorted_unique_df = df.drop_duplicates(subset=[val_col]).sort_values(by=val_col)

        sorted_unique_df[KEY_COLUMN] = sorted_unique_df.apply(
            lambda row: (f"{str(row[prefix_col]).split('/')[0]}_" if prefix_col else "")
            + str(row[name_col]).split("/")[0],
            axis=1,
        )

        # sorted_unique_df = sorted_unique_df.assign(
        #     **{
        #         KEY_COLUMN: (
        #             ((sorted_unique_df[prefix_col] + '_') if prefix_col else '') +
        #             sorted_unique_df[name_col].str.split('/').str[0]  # split on '/' and take the first part (discard French portion)
        #         )
        #     }
        # )

        # drop rows where key or value is NaN
        sorted_unique_df = sorted_unique_df.dropna(subset=[KEY_COLUMN, val_col])

        # tidy up the key column
        sorted_unique_df[KEY_COLUMN] = (
            sorted_unique_df[KEY_COLUMN].apply(cleanstr).str.upper()
        )

        # add a suffix column to ensure unique keys where applicable
        sorted_unique_df[SUFFIX_COLUMN] = sorted_unique_df.groupby(
            KEY_COLUMN
        ).cumcount()
        sorted_unique_df[KEY_COUNT_COLUMN] = sorted_unique_df.groupby(KEY_COLUMN)[
            KEY_COLUMN
        ].transform("count")
        sorted_unique_df[KEY_COLUMN] = sorted_unique_df.apply(
            lambda row: row[KEY_COLUMN]
            + (f"_{row[SUFFIX_COLUMN]}" if row[KEY_COUNT_COLUMN] > 1 else ""),
            axis=1,
        )

        # sort by the key column
        sorted_unique_df = sorted_unique_df.sort_values(by=KEY_COLUMN)

        # cast values to numeric if we are not using StrEnum
        if not isinstance(cls_template, StrEnum):
            sorted_unique_df[val_col] = pd.to_numeric(
                sorted_unique_df[val_col], errors="coerce"
            )

        for _, row in sorted_unique_df.iterrows():
            try:
                name: str = row[name_col]
                value = row[val_col]
                desc: Optional[str] = row[desc_col] if desc_col else None
            except KeyError as e:
                logger.error(
                    f"Missing column in DataFrame: {e}. Columns: {df.columns.tolist()}"
                )
                raise e
            entry = f"{row[KEY_COLUMN]} = "
            if isinstance(cls_template, StrEnum):
                entry += f"'{value}'"
            else:
                entry += f"{value}  # {name}"
            if desc:
                entry += f" ({desc})"
            f.write(" " * indent + f"{entry}\n")

    if not skip_methods:
        for k, v in cls_template.__dict__.items():  # write the methods and properties
            if k.startswith("__") and k.endswith("__"):  # skip dunder methods
                continue
            if skip_auto and (k == "_generate_next_value_"):
                continue
            if inspect.isfunction(v):
                logger.debug(f"[{cls_template.__name__}] found {type(v)} {k}.")
            elif isinstance(v, (property, staticmethod, classmethod)):
                logger.debug(f"[{cls_template.__name__}] found {type(v)} {k}.")
            else:
                continue
            write_method(
                f=f,
                method=v,
                indent=indent,
            )
    logger.debug(f"...wrote class {cls_template.__name__}")


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
        raise FileExistsError(
            f"Module already exists at {fp}. Use 'overwrite=True' to regenerate."
        )
    try:
        with fp.open(mode="w") as f:
            f.write(
                f"# !! This file is automatically generated by: {Path(__file__).name}\n"
            )
            f.write(f"#     date: {datetime.now(tz=timezone.utc).isoformat()}\n\n")
            for import_module, import_items in imports.items():
                if import_items:
                    if isinstance(import_items, str):
                        import_items = [import_items]
                    f.write(f"from {import_module} import {', '.join(import_items)}\n")
            yield f
    finally:
        logger.info(f"Enum file written to {fp}")


def write_module(
    df: pd.DataFrame,
    cls_templates: dict[type[GeoCode], EnumMapSig],
    module_path: Optional[Path] = None,
    imports: Optional[dict[str, Optional[str | set[str]]]] = None,
    overwrite: bool = False,
) -> None:
    """
    Write the GeoCode class definition to the file.
    """
    if imports is None:
        imports = {}
    if module_path is None:
        first_cls = next(iter(cls_templates.keys()))
        module_path = get_module_path(first_cls)
    for t in cls_templates:
        for b in t.__bases__:
            if b.__module__ not in imports:
                imports[b.__module__] = set()
            if isinstance(mod_imports := imports[b.__module__], set):
                mod_imports.add(b.__name__)
            elif isinstance(mod_imports, str):
                mod_imports = {mod_imports, b.__name__}
            else:
                raise TypeError(
                    f"Expected set for imports[{b.__module__}], got {type(imports[b.__module__])}"
                )
            imports[b.__module__] = mod_imports

    with enum_file(
        fp=module_path,
        imports=imports,
        overwrite=overwrite,
    ) as f:
        for cls, mapping in cls_templates.items():
            write_enum_class(
                f=f,
                cls_template=cls,
                df=df,
                mapping=mapping,
            )


def update_imports_dict(
    obj: type | Callable,
    imports: Optional[dict[str, Optional[str | set[str]]]] = None,
) -> dict[str, Optional[str | set[str]]]:
    """
    Update the imports dictionary with a module and its items.
    """
    imports = imports or {}
    try:
        obj_mod: str = obj.__module__
        obj_name: str = obj.__name__
    except AttributeError as e:
        raise ValueError(
            f"Object {obj} does not have a __module__ or __name__ attribute. Ensure it is a class or function."
        ) from e

    if isinstance(mod_imports := imports.get(obj_mod, set()), str):
        mod_imports = {mod_imports}
    elif mod_imports is None:
        raise ValueError(
            f'Module {obj_mod} has already been defined in the imports dict with "None", cannot append {obj_name} to import mapping.'
        )
    mod_imports.add(obj_name)
    imports[obj_mod] = mod_imports
    return imports


def write_geocode_module(
    df: pd.DataFrame,
    cls_templates: dict[type[GeoCode], EnumMapSig],
    module_path: Optional[Path] = None,
    imports: Optional[dict[str, Optional[str | set[str]]]] = None,
    overwrite: bool = False,
):
    imports = update_imports_dict(obj=Schema, imports=imports)

    write_module(
        df=df,
        cls_templates=cls_templates,
        module_path=module_path,
        imports=imports,
        overwrite=overwrite,
    )


class ProvinceTerritory(GeoCode):
    """
    Enum for Canadian provinces and territories.
    This enum is automatically generated from the GeoAttribute data.
    see: https://www12.statcan.gc.ca/census-recensement/2021/geo/ref/domain-domaine/index2021-eng.cfm?lang=e&id=PRUID
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.PR

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 2


class CensusDivision(ProvinceGeoCode):
    """
    Enum for Canadian Census Divisions.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.CD

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 4


class FederalElectoralDistrict(ProvinceGeoCode):
    """
    Enum for Canadian Federal Electoral Districts.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.FED

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 5


class CensusSubdivision(CensusDivisionGeoCode):
    """
    Enum for Canadian Census Subdivisions.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.CSD

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 7


class DesignatedPlace(ProvinceGeoCode):
    """
    Enum for Canadian Designated Places.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.DPL

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 6


class EconomicRegion(ProvinceGeoCode):
    """
    Enum for Canadian Economic Regions.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.ER

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 4


class CensusConsolidatedSubdivision(CensusDivisionGeoCode):
    """
    Enum for Canadian Census Agglomeration Stratified.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.CCS

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 7


class CensusMetropolitanArea(ProvinceGeoCode):
    """
    Enum for Canadian Census Metropolitan Areas.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """Return the Schema for this geo code type."""
        return Schema.CMA

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 3


class CensusTract(CensusMetropolitanAreaGeoCode):
    """
    Enum for Canadian Census Tracts.
    This enum is automatically generated from the GeoAttribute data.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Return the Schema for this geo code type.
        """
        return Schema.CT

    @classmethod
    def get_nchars(cls) -> int:
        """
        Return the number of characters in the code for this enum.
        """
        return 7

    @classmethod
    def get_nprecision(cls) -> int:
        """
        Return the number of decimal places in the code for this enum.
        """
        return 2


if __name__ == "__main__":
    import asyncio
    from statscan.util.log import configure_logging

    configure_logging(level="DEBUG")
    attr_data_file = asyncio.run(download_data(GEO_ATTR_FILE_2021_URL))
    df = unpack_to_dataframe(attr_data_file)

    write_geocode_module(  # write the province/territory enum file
        df=df,
        cls_templates={
            ProvinceTerritory: (
                GeoAttributeColumn2021.PRENAME_PRANOM,  # enum_name_col
                GeoAttributeColumn2021.PRUID_PRIDU,  # enum_value_col
                None,  # enum_desc_col
                None,  # name/key prefix (not used for provinces)
            ),
        },
        # module_path=PR_ENUM_PATH,
        overwrite=True,
    )

    write_geocode_module(  # write the census division enum file
        df=df,
        cls_templates={
            CensusDivision: (
                GeoAttributeColumn2021.CDNAME_DRNOM,  # enum_name_col
                GeoAttributeColumn2021.CDUID_DRIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            ),
        },
        overwrite=True,
    )

    write_geocode_module(  # write the federal electoral district enum file
        df=df,
        cls_templates={
            FederalElectoralDistrict: (
                GeoAttributeColumn2021.FEDNAME_CEFNOM,  # enum_name_col
                GeoAttributeColumn2021.FEDUID_CEFIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            ),
        },
        overwrite=True,
    )

    write_geocode_module(  # write the census subdivision enum file
        df=df,
        cls_templates={
            CensusSubdivision: (
                GeoAttributeColumn2021.CSDNAME_SDRNOM,  # enum_name_col
                GeoAttributeColumn2021.CSDUID_SDRIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            )
        },
        overwrite=True,
    )

    write_geocode_module(  # write the designated place enum file
        df=df,
        cls_templates={
            DesignatedPlace: (
                GeoAttributeColumn2021.DPLNAME_LDNOM,  # enum_name_col
                GeoAttributeColumn2021.DPLUID_LDIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            )
        },
        overwrite=True,
    )

    write_geocode_module(  # write the economic region enum file
        df=df,
        cls_templates={
            EconomicRegion: (
                GeoAttributeColumn2021.ERNAME_RENOM,  # enum_name_col
                GeoAttributeColumn2021.ERUID_REIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            )
        },
        overwrite=True,
    )

    write_geocode_module(
        df=df,
        cls_templates={
            CensusConsolidatedSubdivision: (
                GeoAttributeColumn2021.CCSNAME_SRUNOM,  # enum_name_col
                GeoAttributeColumn2021.CCSUID_SRUIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            )
        },
        overwrite=True,
    )

    write_geocode_module(  # write the census metro area enum file
        df=df[
            pd.to_numeric(
                df[GeoAttributeColumn2021.SACTYPE_CSSGENRE.value], errors="coerce"
            )
            == SACType.CMA.value
        ],
        cls_templates={
            CensusMetropolitanArea: (
                GeoAttributeColumn2021.CMANAME_RMRNOM,  # enum_name_col
                GeoAttributeColumn2021.CMAPUID_RMRPIDU,  # enum_value_col
                None,  # enum_desc_col
                GeoAttributeColumn2021.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
            )
        },
        overwrite=True,
    )

    write_geocode_module(  # write the census tract enum file
        df=df.assign(
            prefix=df[GeoAttributeColumn2021.PREABBR_PRAABBREV]
            + "_"
            + df[GeoAttributeColumn2021.CMANAME_RMRNOM]
        ),
        cls_templates={
            CensusTract: (
                GeoAttributeColumn2021.CTNAME_SRNOM,  # enum_name_col
                GeoAttributeColumn2021.CTUID_SRIDU,  # enum_value_col
                GeoAttributeColumn2021.CMANAME_RMRNOM,  # enum_desc_col
                "prefix",  # name/key prefix (abbreviation of the province)
            )
        },
        overwrite=True,
    )
    logger.info("All GeoCode enums have been written successfully.")
