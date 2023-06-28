from pydantic import BaseModel, Field
from typing import Optional, List


class ModelResourceIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    type: str = Field(..., max_length=36 * 4)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = []


class ModelResourceUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    type: str = Field(None, max_length=36 * 4)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
