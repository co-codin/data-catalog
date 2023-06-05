
from typing import List
from pydantic import Field

from pydantic import BaseModel
from typing import Optional


class ModelIn(BaseModel):
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36*4)
    short_desc: Optional[str] = Field(None, max_length=500)
    business_desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class ModelUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    short_desc: Optional[str] = None
    business_desc: Optional[str] = None
    tags: Optional[List[str]] = None