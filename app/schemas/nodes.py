from typing import List, Tuple, Optional

from pydantic import BaseModel


class NodeIn(BaseModel):
    db: str
    desc: Optional[str]
    name: str


class Attribute(NodeIn):
    attrs: Optional[List[str]]
    dbtype: str


class EntityIn(NodeIn):
    attrs: List[Attribute]


class SatIn(EntityIn):
    ref_table_name: str
    ref_table_pk: str
    fk: str


class OneWayLink(BaseModel):
    desc: Optional[str]
    name: str
    entity_name: str
    entity_pk: str
    fk: str


class LinkIn(BaseModel):
    one_way_links: Tuple[OneWayLink, OneWayLink]
    db: str
    attrs: List[Attribute]
