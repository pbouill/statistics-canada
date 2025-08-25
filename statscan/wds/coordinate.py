
from typing import Any, Generator, Optional

from .member import Member, MemberManager


class Coordinate:
    def __init__(self, coord_str: str, member_manager: Optional[MemberManager] = None):
        self.__coord_str = coord_str
        self.member_manager = member_manager

    @property
    def member_ids(self) -> list[int]:
        return [int(m) for m in str(self).split('.')]
    
    def __getitem__(self, idx) -> Member:
        if self.member_manager is None:
            raise ValueError("MemberManager is not set.")
        return self.member_manager[self.member_ids[idx]]

    def __iter__(self) -> Generator[Member, Any, None]:
        if self.member_manager is None:
            raise ValueError("MemberManager is not set.")
        for member_id in self.member_ids:
            yield self.member_manager[member_id]

    def __str__(self):
        return self.__coord_str

