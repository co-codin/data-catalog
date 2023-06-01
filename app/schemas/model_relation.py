from pydantic import BaseModel, Field
from typing import Optional, List


class ModelRelationIn(BaseModel):
    relationship_group_id: int = Field()
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []
    function: Optional[str] = Field(None, max_length=500)


class ModelRelationUpdateIn(BaseModel):
    name: str = Field(None, max_length=100)
    owner: str = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []
    function: Optional[str] = Field(None, max_length=500)
