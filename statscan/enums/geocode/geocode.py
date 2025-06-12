from enum import Enum, StrEnum, auto

from statscan.enums.schema import Schema


class GeoAttributeColumn2021(StrEnum):
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


class GeoCode(Enum):
    """
    Base class for all geographic codes used in StatsCan DGUIDs.
    """

    @classmethod
    def get_schema(cls) -> Schema:
        """
        Get the schema for this geographic code.

        Returns
        -------
        Schema
            The schema associated with this geographic code.
        """
        raise NotImplementedError(f"{cls.__name__} must implement get_schema()")

    @classmethod
    def get_nchars(cls) -> int:
        """
        Get the number of characters for this geographic code.

        Returns
        -------
        int
            The number of characters in the geographic code.
        """
        raise NotImplementedError(f"{cls.__name__} must implement get_nchars()")

    @property
    def schema(self) -> Schema:
        return self.get_schema()

    @property
    def uid(self) -> str:
        """
        Return the unique identifier for this enum.
        This is usually the last nchar characters of the enum value.
        """
        return f'{self.value:0{self.get_nchars()}}'  # Ensure the UID is zero-padded to nchar length

    @property
    def code(self) -> str:
        """
        Return the geo code for this enum.
        """
        return f'{self.schema.value}{self.uid}'
    

class FloatGeoCode(GeoCode):
    """
    Base class for geographic codes that are represented as floating-point numbers.
    This is useful for geocodes that may have decimal values.
    """

    @classmethod
    def get_nprecision(cls) -> int:
        """
        Get the number of decimal places for this geographic code.

        Returns
        -------
        int
            The number of decimal places in the geographic code.
        """
        raise NotImplementedError(f"{cls.__name__} must implement get_nprecision()")
    
    @property
    def uid(self) -> str:
        """
        Return the unique identifier for this enum as a string with the specified precision.
        This is usually the last nchar characters of the enum value, formatted to nprecision.
        """
        return f'{self.value:0{self.get_nchars()}.{self.get_nprecision()}f}'  # Format to nprecision decimal places