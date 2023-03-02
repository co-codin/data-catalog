from typing import List, Tuple, Optional

from pydantic import BaseModel


class NodeIn(BaseModel):
    db: str
    desc: str
    name: str


class Attribute(NodeIn):
    attrs: Optional[List[str]]
    dbtype: str


class AttributeUpdate(Attribute):
    id: Optional[int]


class EntityIn(NodeIn):
    attrs: List[Attribute]
    uuid: Optional[str]


class EntityUpdateIn(EntityIn):
    attrs: List[AttributeUpdate]


class SatCommon(EntityIn):
    ref_table_pk: str
    fk: str


class SatIn(SatCommon):
    ref_table_uuid: str


class SatUpdateIn(SatCommon):
    attrs: List[AttributeUpdate]


class OneWayLink(BaseModel):
    desc: str
    name: str
    uuid: Optional[str]

    entity_uuid: str
    entity_pk: str
    fk: str


class LinkIn(BaseModel):
    one_way_links: Tuple[OneWayLink, OneWayLink]
    db: str
    attrs: List[Attribute]


class LinkUpdateIn(LinkIn):
    attrs: List[AttributeUpdate]
