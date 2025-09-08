from typing import Any, Generator, Optional
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from .models.member import Member, MemberManager


class Coordinate:
    def __init__(self, coord_str: str, member_manager: Optional[MemberManager] = None):
        self.__coord_str = coord_str
        self.member_manager = member_manager

    @property
    def member_ids(self) -> list[int]:
        return [int(m) for m in str(self).split('.')]

    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        source_type: Any, 
        handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Defines the Pydantic V2 Core Schema for the Coordinate class.

        This schema tells Pydantic to:
        1.  Expect a string as input.
        2.  Call this class's constructor (`__init__`) with the string to validate it and create an instance.
        3.  Also allow instances of `Coordinate` to pass through validation unmodified.
        """
        # This validator function will be called with the input string
        # and should return an instance of Coordinate.
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(cls), from_str_schema]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

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
