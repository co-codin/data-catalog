from pydantic import BaseModel, Field
from typing import Optional, List, Any

from app.schemas.access_label import AccessLabelIn


class ModelResourceIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    type: str = Field(..., max_length=36 * 4)
    db_link: str | None = None
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = []
    access_label: Optional[AccessLabelIn] = None


class ModelResourceUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    type: str = Field(None, max_length=36 * 4)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    access_label: Optional[AccessLabelIn] = None


class ModelResourceOutRelIn(BaseModel):
    name: str
    guid: str

    class Config:
        orm_mode = True
