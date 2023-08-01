from __future__ import annotations
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.queries import QueryFilterType, QueryRunningStatus, QueryRunningPublishStatus
from app.schemas.tag import TagOut


class Operator(Enum):
    EQ = '='
    LT = '<'
    GT = '>'
    LE = '<='
    GE = '>='
    BETWEEN = 'between'
    IN = 'in'
    IS_NULL = 'is null'
    LIKE = 'like'


class BooleanOperator(Enum):
    AND = 'and'
    OR = 'or'
    NOT = 'not'


class AggregateFunc(Enum):
    SUM = 'sum'
    MIN = 'min'
    MAX = 'max'
    AVG = 'avg'
    COUNT = 'count'


class Attr(BaseModel):
    db_link: str = Field(None, min_length=1)
    display: bool


class AliasAttr(BaseModel):
    attr: Attr


class Aggregate(BaseModel):
    function: AggregateFunc
    db_link: str
    display: bool

    class Config:
        use_enum_values = True


class AliasAggregate(BaseModel):
    aggregate: Aggregate


class SimpleFilter(BaseModel):
    alias: str = Field(..., min_length=1)
    operator: Operator
    value: (
            int | float | str | bool | datetime
            | list[int] | list[float] | list[str] | list[bool] | list[datetime]
    )

    class Config:
        use_enum_values = True


class BooleanFilter(BaseModel):
    operator: BooleanOperator
    values: list[SimpleFilter | BooleanFilter]

    class Config:
        use_enum_values = True


class QueryIn(BaseModel):
    name: str = Field(..., min_length=1)
    owner_guid: str
    desc: str | None = None
    model_version_id: int
    model_resource_id: int
    
    filter_type: QueryFilterType

    filters_displayed: str = Field(..., min_length=1)
    having_displayed: str = Field(..., min_length=1)

    tags: list[str] = []

    aliases: dict[str, AliasAttr | AliasAggregate]
    filter: SimpleFilter | BooleanFilter | None = None
    having: SimpleFilter | BooleanFilter | None = None

    run_immediately: bool
    distinct: bool = Field(..., alias='unique_only')

    class Config:
        use_enum_values = True


class QueryUpdateIn(BaseModel):
    name: str | None = None
    owner_guid: str | None = None
    desc: str | None = None
    model_version_id: int | None = None
    model_resource_id: int | None = None
    filter_type: QueryFilterType | None = None

    filters_displayed: str | None = None
    having_displayed: str | None = None

    tags: list[str] = []

    aliases: dict[str, AliasAttr | AliasAggregate] | None = None
    filter: SimpleFilter | BooleanFilter | None = None
    having: SimpleFilter | BooleanFilter | None = None

    run_immediately: bool | None = None

    class Config:
        use_enum_values = True


class QueryManyOut(BaseModel):
    id: int
    guid: str

    name: str
    desc: str | None = None
    model_name: str
    updated_at: datetime
    status: QueryRunningStatus
    tags: list[TagOut] = []

    author_first_name: str | None = None
    author_last_name: str | None = None
    author_middle_name: str | None = None
    author_email: str | None = None

    class Config:
        orm_mode = True


class QueryModelManyOut(BaseModel):
    id: int
    guid: str
    name: str

    class Config:
        orm_mode = True


class QueryModelVersionManyOut(BaseModel):
    id: str
    guid: str
    version: str | None

    class Config:
        orm_mode = True


class QueryModelResourceManyOut(BaseModel):
    id: str
    guid: str
    name: str

    class Config:
        orm_mode = True


class QueryModelResourceAttributeOut(BaseModel):
    id: int
    guid: str
    name: str
    db_link: str
    json_db_link: str

    class Config:
        orm_mode = True


class QueryOut(BaseModel):
    id: int
    guid: str

    status: QueryRunningStatus
    name: str
    desc: str | None = None

    filters_displayed: str | None = None
    having_displayed: str | None = None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []

    json_: str = Field(..., alias='json')

    class Config:
        orm_mode = True


class FullQueryOut(QueryOut):
    owner: str
    attrs: list[QueryModelResourceAttributeOut]
    model: QueryModelManyOut
    model_version: QueryModelVersionManyOut
    model_resource: QueryModelResourceManyOut


class QueryExecutionOut(BaseModel):
    id: int
    guid: str

    status: QueryRunningStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    publish_name: str | None = None
    publish_status: QueryRunningPublishStatus | None = None

    class Config:
        orm_mode = True


class LinkedResourcesIn(BaseModel):
    resource_guid: str
    model_version_id: int = Field(..., gt=0)


class ModelResourceOut(BaseModel):
    id: int
    guid: str
    name: str
    db_link: str

    class Config:
        orm_mode = True
