import logging

from pydantic import BaseModel, model_validator


logger = logging.getLogger(__name__)


class Base(BaseModel):
    @classmethod
    def _preprocess_data(cls, data: dict) -> dict:
        """
        Hook for subclasses to preprocess data before validation.
        Override this method in subclasses to clean up data.
        """
        return data

    @model_validator(mode="before")
    @classmethod
    def process_data(cls, data: dict) -> dict:
        """
        Check for extra fields in the data dictionary that are not defined in the model.
        First allows subclasses to preprocess the data.
        """
        # Handle None data
        if data is None:
            return {}

        # Handle non-dict data
        if not isinstance(data, dict):
            logger.warning(
                f"[{cls.__name__}] Expected dict but got {type(data)}: {data}"
            )
            return {}

        # Let subclasses preprocess the data first
        data = cls._preprocess_data(data)

        extra_fields = set(data.keys()) - set(cls.model_fields.keys())
        if extra_fields:
            # Check if any of the extra fields are aliases of existing fields
            field_aliases = {
                field_info.alias
                for field_info in cls.model_fields.values()
                if field_info.alias
            }
            # Remove fields that are actually aliases from the extra fields
            extra_fields -= field_aliases

        if extra_fields:
            logger.warning(f"[{cls.__name__}] Extra fields found: {extra_fields}")
        return data
