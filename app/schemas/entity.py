from typing import List, Optional

from app.schemas.field import Field, FieldUpdate
from app.schemas.node import NodeIn


class EntityIn(NodeIn):
    fields: List[Field]
    uuid: Optional[str]


class EntityUpdateIn(NodeIn):
    fields: List[FieldUpdate]
