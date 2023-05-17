
from ast import List
from dataclasses import Field

from pydantic import BaseModel
from pyparsing import Optional


class ModelIn(BaseModel):
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []
