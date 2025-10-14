
"""Member model and manager for WDS API responses."""

from collections.abc import Iterator
from typing import Any

from pydantic import field_validator

from statscan.enums.auto.wds.classification_type import ClassificationType

from .base import WDSBaseModel


class Member(WDSBaseModel):
    """Represents a member in WDS API responses."""

    memberId: int
    parentMemberId: int | None = None  # API can return null
    memberNameEn: str
    memberNameFr: str
    classificationCode: int | str | None = None  # API returns int or string
    classificationTypeCode: ClassificationType | int | str | None = (
        None  # API returns string
    )
    geoLevel: int | None = None  # API can return null
    vintage: int | None = None  # API can return null
    terminated: bool
    memberUoMCode: int | None = None

    @field_validator("classificationTypeCode", mode="before")
    @classmethod
    def convert_classification_type(cls, v: Any) -> ClassificationType | int | None:
        """Convert string classification type codes to enum values."""
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
    """Manages a collection of Member objects."""

    def __init__(self, members: list[Member] | None = None):
        """Initialize the MemberManager with a list of members."""
        if members is None:
            members = []
        self.__members = members

    def add_member(self, member: Member, replace: bool = False) -> None:
        """Add a member, optionally replacing an existing one."""
        if (existing_member := self.members.get(member.memberId)) is not None:
            if not replace:
                raise ValueError(
                    f"Member with ID {member.memberId} already exists. "
                    f"Cannot add {member}"
                )
            else:
                self.remove_member(existing_member)
        self.__members.append(member)

    def remove_member(self, member: int | Member) -> None:
        """Remove a member by ID or instance."""
        if isinstance(member, int):
            member = self[member]
        self.__members.remove(member)

    @property
    def members(self) -> dict[int, Member]:
        """Return a dictionary of members keyed by memberId."""
        return {member.memberId: member for member in self.__members}

    def __getitem__(self, member_id: int) -> Member:
        """Get a member by ID."""
        if (member := self.members.get(member_id)) is None:
            raise KeyError(f"Member with ID {member_id} does not exist.")
        return member

    def __setitem__(self, member_id: int, member: Member) -> None:
        """Set a member by ID."""
        if (existing_member := self.members.get(member_id)) is not None:
            self.__members.remove(existing_member)
        self.__members.append(member)

    def __iter__(self) -> Iterator[Member]:
        """Iterate over members."""
        return iter(self.__members)
