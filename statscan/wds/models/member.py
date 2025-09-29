from typing import Iterator, Optional, Any

from pydantic import field_validator

from statscan.enums.auto.wds.classification_type import ClassificationType

from .base import WDSBaseModel


class Member(WDSBaseModel):
    memberId: int
    parentMemberId: Optional[int] = None  # API can return null
    memberNameEn: str
    memberNameFr: str
    classificationCode: Optional[int] = None  # API can return null
    classificationTypeCode: Optional[ClassificationType | int | str] = (
        None  # API returns string
    )
    geoLevel: Optional[int] = None  # API can return null
    vintage: Optional[int] = None  # API can return null
    terminated: bool
    memberUoMCode: Optional[int] = None

    @field_validator("classificationTypeCode", mode="before")
    @classmethod
    def convert_classification_type(cls, v: Any) -> Optional[ClassificationType | int]:
        """Convert string classification type codes to enum values"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return ClassificationType(int(v))
            except (ValueError, TypeError):
                # If enum conversion fails, return as int
                try:
                    return int(v)
                except (ValueError, TypeError):
                    return None
        return v


class MemberManager:
    def __init__(self, members: list[Member] = []):
        self.__members = members

    def add_member(self, member: Member, replace: bool = False) -> None:
        if (existing_member := self.members.get(member.memberId)) is not None:
            if not replace:
                raise ValueError(
                    f"Member with ID {member.memberId} already exists. Cannot add {member}"
                )
            else:
                self.remove_member(existing_member)
        self.__members.append(member)

    def remove_member(self, member: int | Member) -> None:
        if isinstance(member, int):
            member = self[member]
        self.__members.remove(member)

    @property
    def members(self) -> dict[int, Member]:
        return {member.memberId: member for member in self.__members}

    def __getitem__(self, member_id: int) -> Member:
        if (member := self.members.get(member_id)) is None:
            raise KeyError(f"Member with ID {member_id} does not exist.")
        return member

    def __setitem__(self, member_id: int, member: Member) -> None:
        if (existing_member := self.members.get(member_id)) is not None:
            self.__members.remove(existing_member)
        self.__members.append(member)

    def __iter__(self) -> Iterator[Member]:
        return iter(self.__members)
