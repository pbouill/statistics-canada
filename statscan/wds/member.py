from typing import Optional

from pydantic import BaseModel

from statscan.enums.auto.wds.classification_type import ClassificationType
from statscan.enums.auto.wds.uom import UoM


class Member(BaseModel):
    memberId: int
    parentMemberId: int
    memberNameEn: str
    memberNameFr: str
    classificationCode: int  # TODO: should be Enum
    classificationTypeCode: ClassificationType  # TODO: should be Enum
    geoLevel: int  # TODO: should be Enum
    vintage: int
    terminated: bool
    memberUoMCode: Optional[int] = None