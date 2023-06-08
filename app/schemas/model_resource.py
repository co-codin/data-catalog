from pydantic import BaseModel, Field, validator
from typing import Optional, List


class ModelResourceIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36 * 4)
    type: str = Field(..., max_length=36 * 4)
    db_link: Optional[str] = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class ModelResourceUpdateIn(BaseModel):
    name: str = Field(None, max_length=100)
    owner: str = Field(None, max_length=36 * 4)
    type: str = Field(None, max_length=36 * 4)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None

class ResourceAttributeIn(BaseModel):
    resource_id: int
    name: str = Field(None, max_length=100)
    key: Optional[bool] = Field(None)
    db_link: Optional[str] = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    data_type_id: int = Field()
    data_type_flag: int
    cardinality: str
    parent_id: Optional[int] = Field(None)
    tags: Optional[List[str]] = []

    @validator('data_type_flag')
    def data_type_flag_validator(cls, v):
        accepted = [0, 1]
        if v not in accepted:
            raise ValueError('Invalid data_type_flag')

        return v

    @validator('cardinality')
    def cardinality_validator(cls, v):
        accepted = ["0..1", "1..1", "1..*", "0..*"]
        if v not in accepted:
            raise ValueError('Invalid cardinality')

        return v


class ResourceAttributeUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    key: Optional[bool] = Field(None)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    data_type_id: Optional[int] = Field(None)
    data_type_flag: Optional[int] = Field(None)
    cardinality: Optional[str] = Field(None)
    parent_id: Optional[int] = Field(None)
    tags: Optional[List[str]] = Field(None)


    @validator('data_type_flag')
    def data_type_flag_validator(cls, v):
        accepted = [0, 1]
        if v not in accepted:
            raise ValueError('Invalid data_type_flag')

        return v

    @validator('cardinality')
    def cardinality_validator(cls, v):
        accepted = ["0..1", "1..1", "1..*", "0..*"]
        if v not in accepted:
            raise ValueError('Invalid cardinality')

        return v
