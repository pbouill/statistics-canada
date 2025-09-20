from datetime import datetime, date
from typing import Optional, Any

from pydantic import field_validator

from statscan.enums.wds.wds_response_status import WDSResponseStatus
from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.subject import Subject
from statscan.enums.auto.wds.survey import Survey
from statscan.enums.auto.wds.status import Status

from .base import WDSBaseModel
from .footnote import Footnote
from .dimension import Dimension
from .correction import Correction



class CubeExistsError(ValueError):
    pass


class Cube(WDSBaseModel):
    # base cube (lite) attributes
    responseStatusCode: Optional[WDSResponseStatus] = None
    productId: int
    cansimId: Optional[str] = None
    cubeTitleEn: str
    cubeTitleFr: str
    cubeStartDate: datetime
    cubeEndDate: datetime

    releaseTime: datetime
    archiveStatusCode: Optional[Status] = None  # TODO: should be Enum, looks like field can also be named "archived"
    archiveStatusEn: Optional[str] = None
    archiveStatusFr: Optional[str] = None
    subjectCode: Optional[list[Subject]]
    surveyCode: Optional[list[Survey]] = None
    frequencyCode: Frequency
    corrections: list[Correction]  # TODO: proper typing required, looks like field can also be named "correctionFootnote" or "correction"
    issueDate: Optional[datetime] = None

    # full cube attributes
    nbSeriesCube: Optional[int] = None
    nbDatapointsCube: Optional[int] = None
    dimensions: Optional[list[Dimension]] = None
    geoAttribute: Optional[list] = None  # TODO: proper typing required

    @field_validator("subjectCode", "surveyCode", mode="before")
    @classmethod
    def convert_str_list_to_int_list(cls, v: Any) -> list[int]:
        """
        Takes the incoming list of string numbers and converts each
        element to an integer before standard validation runs.
        """
        if isinstance(v, list):
            # This list comprehension is the intermediary step you need
            return [int(item) for item in v]
        return v


class CubeManager:
    def __init__(self, cubes: Optional[list[Cube]] = None):
        self.__cubes: list[Cube] = cubes or []

    @property
    def cubes(self) -> dict[int, Cube]:
        return {cube.productId: cube for cube in self.__cubes}

    @property
    def latest_cube(self) -> Optional[Cube]:
        if not self.__cubes:
            return None
        return max(self.__cubes, key=lambda c: c.releaseTime)
    
    @property
    def product_ids(self) -> set[int]:
        return {cube.productId for cube in self.__cubes}
    
    def update_cube(self, cube: Cube) -> bool:
        """
        Update an existing cube in the manager.
        Args:
            cube (Cube): The cube to update or add.
        Returns:
            bool: True if the cube was updated, False if no changes were made.
        """
        if (existing_cube := self.cubes.get(cube.productId)) is not None:
            if existing_cube == cube:
                return False  # No changes
            else:
                self[cube.productId] = cube
            return True
        else:
            raise KeyError(f"Cube with product ID {cube.productId} does not exist.")

    def add_cube(self, cube: Cube, replace: bool = False) -> bool:
        """
        Add a cube to the manager. If a cube with the same productId already exists,
        it will not be added unless `replace` is set to True.
        
        Args:
            cube (Cube): The cube to add.
            replace (bool): Whether to replace an existing cube with the same productId.
        Returns:
            bool: True if the cube was added or updated.
        """
        if cube.productId in self.product_ids:
            if not replace:
                raise CubeExistsError(f"Cube with product ID {cube.productId} already exists. Cannot add {cube}")
            else:
                return self.update_cube(cube)
        else:
            self.__cubes.append(cube)
            return True

    def remove_cube(self, cube: int | Cube) -> None:
        if isinstance(cube, int):
            cube = self[cube]
        self.__cubes.remove(cube)

    def __getitem__(self, product_id: int) -> Cube:
        if (cube := self.cubes.get(product_id)) is None:
            raise KeyError(f"Cube with product ID {product_id} does not exist.")
        return cube

    def __setitem__(self, product_id: int, cube: Cube) -> None:
        if (existing_cube := self.cubes.get(product_id)) is not None:
            self.__cubes.remove(existing_cube)
        self.__cubes.append(cube)

    def __iter__(self):
        return iter(self.__cubes)
