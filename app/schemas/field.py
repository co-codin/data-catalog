from typing import Optional, List

from app.schemas.node import NodeIn


class Field(NodeIn):
    attrs: Optional[List[str]]
    dbtype: str


class FieldUpdate(Field):
    id: Optional[int]
