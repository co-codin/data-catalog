from typing import List, Tuple, Optional

from pydantic import BaseModel


class NodeIn(BaseModel):
    db: str
    desc: str
    name: str


class Field(NodeIn):
    attrs: Optional[List[str]]
    dbtype: str


class FieldUpdate(Field):
    id: Optional[int]


class EntityIn(NodeIn):
    fields: List[Field]
    uuid: Optional[str]


class EntityUpdateIn(NodeIn):
    fields: List[FieldUpdate]


class SatRelationship(BaseModel):
    ref_table_uuid: str
    ref_table_pk: str
    fk: str


class SatIn(EntityIn, SatRelationship):
    ...


class SatUpdateIn(NodeIn, SatRelationship):
    ref_table_uuid: Optional[str]
    fields: List[FieldUpdate]


class OneWayLink(BaseModel):
    desc: str
    name: str
    entity_uuid: str
    entity_pk: str
    fk: str


class LinkIn(BaseModel):
    one_way_links: Tuple[OneWayLink, OneWayLink]
    db: str
    fields: List[Field]


class LinkUpdateIn(LinkIn):
    fields: List[FieldUpdate]
