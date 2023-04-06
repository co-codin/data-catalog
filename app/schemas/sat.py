from typing import Optional, List

from pydantic import BaseModel

from app.schemas.entity import EntityIn
from app.schemas.field import FieldUpdate
from app.schemas.node import NodeIn


class SatRelationship(BaseModel):
    ref_table_uuid: str
    ref_table_pk: str
    fk: str


class SatIn(EntityIn, SatRelationship):
    ...


class SatUpdateIn(NodeIn, SatRelationship):
    ref_table_uuid: Optional[str]
    fields: List[FieldUpdate]
