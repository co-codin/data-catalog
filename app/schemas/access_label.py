from pydantic import BaseModel, Field, validator

from app.enums.enums import AccessLabelType


class AccessLabelIn(BaseModel):
    type: str | None = Field(None, max_length=15)
    operation_version_id: int | None = Field(None)

    @validator('type')
    def cardinality_validator(cls, v):
        accepted = [type.value for type in AccessLabelType]
        if v and (v not in accepted):
            raise ValueError('Invalid access label type')

        return v
