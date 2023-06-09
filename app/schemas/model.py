from typing import List
from pydantic import Field

from pydantic import BaseModel
from typing import Optional


class ModelCommon(BaseModel):
    name: str = Field(..., max_length=100)
    short_desc: str | None = Field(None, max_length=500)
    business_desc: str | None = Field(None, max_length=500)
    tags: list[str] = []


class ModelIn(ModelCommon):
    owner: str = Field(..., max_length=36*4)


class ModelUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    short_desc: Optional[str] = None
    business_desc: Optional[str] = None
    tags: Optional[List[str]] = None
