from pathlib import Path
from sys import prefix
from typing import Iterable, Optional, TextIO, Generator, Callable, Any
from datetime import datetime, timezone
import re
from enum import Enum, StrEnum, auto
import asyncio
import logging
from contextlib import contextmanager
import inspect

import pandas as pd

import statscan.enums.auto
from statscan.enums.geolevel import GeoLevel
from statscan.url import GEO_ATTR_FILE_2021_URL
from statscan.util.data import download_data, unpack_to_dataframe

logger = logging.getLogger(__name__)

AUTO_ENUMS_PATH = Path(statscan.enums.auto.__file__).parent


class GeoAttributeColumn(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        """
        Return the lower-cased version of the member name.
        """
        return name.upper()

    PRUID_PRIDU = auto()
    PRDGUID_PRIDUGD = auto()
    PRNAME_PRNOM = auto()
    PRENAME_PRANOM = auto()
    PRFNAME_PRFNOM = auto()  # French
    PREABBR_PRAABBREV = auto()
    PRFABBR_PRFABBREV = auto()  # French
    CDUID_DRIDU = auto()
    CDDGUID_DRIDUGD = auto()
    CDNAME_DRNOM = auto()
    CDTYPE_DRGENRE = auto()
    FEDUID_CEFIDU = auto()
    FEDDGUID_CEFIDUGD = auto()
    FEDNAME_CEFNOM = auto()
    CSDUID_SDRIDU = auto()
    CSDDGUID_SDRIDUGD = auto()
    CSDNAME_SDRNOM = auto()
    CSDTYPE_SDRGENRE = auto()
    DPLUID_LDIDU = auto()
    DPLDGUID_LDIDUGD = auto()
    DPLNAME_LDNOM = auto()
    DPLTYPE_LDGENRE = auto()
    ERUID_REIDU = auto()
    ERDGUID_REIDUGD = auto()
    ERNAME_RENOM = auto()
    CCSUID_SRUIDU = auto()
    CCSDGUID_SRUIDUGD = auto()
    CCSNAME_SRUNOM = auto()
    SACTYPE_CSSGENRE = auto()
    SACCODE_CSSCODE = auto()
    CMAPUID_RMRPIDU = auto()
    CMAPDGUID_RMRPIDUGD = auto()
    CMAUID_RMRIDU = auto()
    CMADGUID_RMRIDUGD = auto()
    CMANAME_RMRNOM = auto()
    CMATYPE_RMRGENRE = auto()
    CTUID_SRIDU = auto()
    CTDGUID_SRIDUGD = auto()
    CTCODE_SRCODE = auto()
    CTNAME_SRNOM = auto()
    POPCTRRAPUID_CTRPOPRRPIDU = auto()
    POPCTRRAPDGUID_CTRPOPRRPIDUGD = auto()
    POPCTRRAUID_CTRPOPRRIDU = auto()
    POPCTRRADGUID_CTRPOPRRIDUGD = auto()
    POPCTRRANAME_CTRPOPRRNOM = auto()
    POPCTRRATYPE_CTRPOPRRGENRE = auto()
    POPCTRRACLASS_CTRPOPRRCLASSE = auto()
    DAUID_ADIDU = auto()
    DADGUID_ADIDUGD = auto()
    DARPLAMX_ADLAMX = auto()
    DARPLAMY_ADLAMY = auto()
    DARPLAT_ADLAT = auto()
    DARPLONG_ADLONG = auto()
    DBUID_IDIDU = auto()
    DBDGUID_IDIDUGD = auto()
    DBPOP2021_IDPOP2021 = auto()
    DBTDWELL2021_IDTLOG2021 = auto()
    DBURDWELL2021_IDRHLOG2021 = auto()
    DBAREA2021_IDSUP2021 = auto()
    DBIR2021_IDRI2021 = auto()
    ADAUID_ADAIDU = auto()
    ADADGUID_ADAIDUGD = auto()
    ADACODE_ADACODE = auto()


EnumMapSig = tuple[
    GeoAttributeColumn,  # enum_name_col
    GeoAttributeColumn,  # enum_value_col
    Optional[GeoAttributeColumn],  # enum_desc_col
    Optional[GeoAttributeColumn],  # name/key prefix
]


def cleanstr(s: str) -> str:
    """
    Clean a string by removing leading/trailing whitespace and converting to uppercase.
    """
    for char in (' ', '-'): # Replace spaces, hyphens, and periods with underscores
        s = s.replace(char, '_')

    for char in ("'", '"', '.'):  # Remove apostrophes, quotes, and periods
        s = s.replace(char, '')

    s = re.sub(r'[^\w_]+', '', s)  # Remove any characters that are not alphanumeric or underscore
    s = re.sub(r'_+', '_', s)  # Replace multiple underscores with a single underscore

    s = s.strip('_')  # Remove leading or trailing underscores that might have been created
    
    if s and s[0].isdigit():  # Ensure the name does not start with a digit
        s = '_' + s
    return s


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

    logger.debug(f'Writing class {cls_name} to file from template {cls_template}...')
    indent = 4

    f.write('\n\n')
    f.write(f'class {cls_name}({", ".join(b.__name__ for b in cls_bases)}):\n')
    f.write(f'    """\n')
    f.write(f'    Automatically generated Enum for {cls_name}\n')
    if mapping is not None:
        name_col, val_col, desc_col, prefix_col = mapping
        f.write(f'    Name: {name_col}\n')
        f.write(f'    Value: {val_col}\n')
        if desc_col:
            f.write(f'    Description: {desc_col}\n')
        if prefix_col:
            f.write(f'    Prefix: {prefix_col}\n')
    f.write(f'    """\n')

    if df is not None:
        if mapping is None:
            raise ValueError("Mapping must be provided if DataFrame is provided.")
        # drop duplicate values and sort by name (do not consider description for uniqueness), but ensure all other columns are preserved...
        sorted_unique_df = df.drop_duplicates(subset=[val_col.value]).sort_values(by=name_col.value)
        if prefix_col:
            sorted_unique_df = sorted_unique_df.sort_values(by=[prefix_col.value, name_col.value])
        
        for _, row in sorted_unique_df.iterrows():
            try:
                name: str = row[name_col.value]
                value = row[val_col.value]
                desc: Optional[str] = row[desc_col.value] if desc_col else None
                prefix: Optional[str] = row[prefix_col.value] if prefix_col else None
            except KeyError as e:
                logger.error(f"Missing column in DataFrame: {e}. Columns: {df.columns.tolist()}")
                raise e
            key = cleanstr(name.split('/')[0]).upper()
            entry = ''
            if prefix:
                entry += cleanstr(prefix).upper() + '_'
            entry += f'{key} = '
            if isinstance(cls_template, StrEnum):
                entry += f"'{value}'"
            else:
                entry += f'{value}  # {name}'
            if desc:
                entry += f" ({desc})"
            f.write(' ' * indent + f'{entry}\n')

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
    imports: dict[str, Optional[str | Iterable[str]]],
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


class ProvinceTerritory(Enum):
    """
    Enum for Canadian provinces and territories.
    This enum is automatically generated from the GeoAttribute data.
    """
    
    @staticmethod
    def get_geo_level() -> GeoLevel:
        """
        Return the GeoLevel for this enum.
        """
        return GeoLevel.PR

    @property
    def dguid(self) -> str:
        """
        Return the DGUID for this enum.
        """
        return f'2021{self.get_geo_level().value}{self.value:02d}'
    

def write_province_enums(df: pd.DataFrame, overwrite: bool = False) -> Path:
    """
    Write the province enums to a file.
    """
    fp = AUTO_ENUMS_PATH / 'province.py'
    mapping: EnumMapSig = (
        GeoAttributeColumn.PRENAME_PRANOM,  # enum_name_col
        GeoAttributeColumn.PRUID_PRIDU,  # enum_value_col
        None,  # enum_desc_col
        None, # name/key prefix (not used for provinces)
    )
    with enum_file(
        fp=fp,
        imports={
            'enum': ProvinceTerritory.__bases__[0].__name__,  # Enum or StrEnum
            'statscan.enums.geolevel': GeoLevel.__name__,
        },
        overwrite=overwrite
    ) as f:
        write_enum_class(
            f=f,
            cls_template=ProvinceTerritory,
            df=df,
            mapping=mapping,
        )
    return fp


class CensusDivision(Enum):
    """
    Enum for Canadian Census Divisions.
    This enum is automatically generated from the GeoAttribute data.
    """

    @staticmethod
    def get_geo_level() -> GeoLevel:
        """
        Return the GeoLevel for this enum.
        """
        return GeoLevel.CD
    
    @property
    def province_territory(self) -> ProvinceTerritory:
        """
        Return the ProvinceTerritory for this enum.
        """
        return ProvinceTerritory(int(str(self.value)[:2]))

    @property
    def dguid(self) -> str:
        """
        Return the DGUID for this enum.
        """
        return f'2021{self.get_geo_level().value}{self.value:04d}'


def write_census_division_enums(
    df: pd.DataFrame, 
    overwrite: bool = False,
) -> Path:
    mapping = (
        GeoAttributeColumn.CDNAME_DRNOM,  # enum_name_col
        GeoAttributeColumn.CDUID_DRIDU,  # enum_value_col
        None,  # enum_desc_col
        GeoAttributeColumn.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
    )
    fp = AUTO_ENUMS_PATH / 'census_division.py'

    with enum_file(
        fp=fp,
        imports={
            'enum': Enum.__name__,
            'statscan.enums.geolevel': GeoLevel.__name__,
            'statscan.enums.auto.province': ProvinceTerritory.__name__,
        },
        overwrite=overwrite,
    ) as f:
        write_enum_class(f=f, cls_template=CensusDivision, df=df, mapping=mapping)
    return fp


class FederalElectoralDistrict(Enum):
    """
    Enum for Canadian Federal Electoral Districts.
    This enum is automatically generated from the GeoAttribute data.
    """

    @staticmethod
    def get_geo_level() -> GeoLevel:
        """
        Return the GeoLevel for this enum.
        """
        return GeoLevel.FED
    
    @property
    def province_territory(self) -> ProvinceTerritory:
        """
        Return the ProvinceTerritory for this enum.
        """
        return ProvinceTerritory(int(str(self.value)[:2]))

    @property
    def dguid(self) -> str:
        """
        Return the DGUID for this enum.
        """
        return f'2021{self.get_geo_level().value}{self.value:05d}'
    
def write_federal_electoral_district_enums(
    df: pd.DataFrame, 
    overwrite: bool = False,
) -> Path:
    """
    Write the federal electoral district enums to a file.
    """
    fp = AUTO_ENUMS_PATH / 'federal_electoral_district.py'
    mapping = (
        GeoAttributeColumn.FEDNAME_CEFNOM,  # enum_name_col
        GeoAttributeColumn.FEDUID_CEFIDU,  # enum_value_col
        None,  # enum_desc_col
        GeoAttributeColumn.PREABBR_PRAABBREV,  # name/key prefix (abbreviation of the province)
    )
    with enum_file(
        fp=fp,
        imports={
            'enum': Enum.__name__,
            'statscan.enums.geolevel': GeoLevel.__name__,
            'statscan.enums.auto.province': ProvinceTerritory.__name__,
        },
        overwrite=overwrite,
    ) as f:
        write_enum_class(f=f, cls_template=FederalElectoralDistrict, df=df, mapping=mapping)
    return fp


if __name__ == '__main__':
    from statscan.util.log import configure_logging
    configure_logging(level='DEBUG')
    attr_data_file = asyncio.run(download_data(GEO_ATTR_FILE_2021_URL))
    df = unpack_to_dataframe(attr_data_file)

    write_province_enums(df=df, overwrite=True)
    write_census_division_enums(df=df, overwrite=True)
    write_federal_electoral_district_enums(df=df, overwrite=True)
