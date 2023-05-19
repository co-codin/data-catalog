
from typing import List
from pydantic import Field

from pydantic import BaseModel
from typing import Optional


class ModelIn(BaseModel):
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class ModelManyOut(BaseModel):
    pass


class ModelOut(BaseModel):
    pass