from typing import Optional, List

from pydantic import BaseModel

from app.schemas.field import Field, FieldUpdate
from app.schemas.sat import SatRelationship


class OneWayLink(SatRelationship):
    desc: str
    name: str


class OneWayLinkUpdate(OneWayLink):
    ref_table_uuid: Optional[str]


class LinkCommon(BaseModel):
    db: str
    fields: List[Field]
    main_link: OneWayLink
    paired_link: OneWayLink


class LinkIn(LinkCommon):
    uuid: Optional[str]


class LinkUpdateIn(LinkCommon):
    main_link: OneWayLinkUpdate
    paired_link: OneWayLinkUpdate
    fields: List[FieldUpdate]
