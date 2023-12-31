from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from app.schemas.tag import TagOut


class OperationParameterIn(BaseModel):
    name: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    model_data_type_id: int = Field(..., ge=1)


class OperationIn(BaseModel):
    name: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None


class OperationBodyIn(BaseModel):
    owner: str
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    input: List[OperationParameterIn]
    output: OperationParameterIn
    code: str = Field(..., min_length=1, max_length=10 ** 8)


class OperationBodyUpdateIn(OperationBodyIn):
    confirm: bool = False

class ConfirmIn(BaseModel):
    confirm: bool = False

class WarningOut(BaseModel):
    in_relations: int
    in_attributes: int


class OperationBodyOut(BaseModel):
    operation_body_id: int
    guid: str
    version: int
    owner: str
    desc: str
    tags: Optional[List[str]] = []

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class OperationManyOut(BaseModel):
    guid: str

    name: str
    owner: str
    desc: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []

    class Config:
        orm_mode = True


class OperationBodyInfoOut(BaseModel):
    guid: str
    version: int


class OperationOut(BaseModel):
    name: str
    owner: str
    desc: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    last_version: OperationBodyInfoOut | None

    class Config:
        orm_mode = True
