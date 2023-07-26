import uuid

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.models import ModelVersion


class QueryRunningStatus(Enum):
    CREATED = 'created'
    RUNNING = 'running'
    DONE = 'done'
    CANCELED = 'canceled'
    ERROR = 'error'


class QueryFilterType(Enum):
    CONSTRUCTOR = 'constructor'
    JSON = 'json'


class QueryRunningPublishStatus(Enum):
    PUBLISHING = 'publishing'
    PUBLISHED = 'published'
    ERROR = 'error'


query_viewers = Table(
    'query_query_viewers',
    Base.metadata,
    Column("query_id", ForeignKey("queries.id"), primary_key=True),
    Column("viewer_id", ForeignKey("query_viewers.id"), primary_key=True)
)

query_tags = Table(
    'query_tags',
    Base.metadata,
    Column('query_id', ForeignKey('queries.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True)
)


class QueryViewer(Base):
    __tablename__ = 'query_viewers'

    id = Column(BigInteger, nullable=False, unique=True, index=True, autoincrement=True, primary_key=True)
    guid = Column(String(100), nullable=False, unique=True)

    queries = relationship('Query', secondary=query_viewers)


class Query(Base):
    __tablename__ = 'queries'

    id = Column(BigInteger, nullable=False, unique=True, index=True, autoincrement=True, primary_key=True)
    guid = Column(String(100), nullable=False, unique=True, index=True, default=str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    desc = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)

    filter_type = Column(String, nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    json = Column(JSON, nullable=False)

    filters_displayed = Column(Text, nullable=False)
    having_displayed = Column(Text, nullable=False)

    owner_guid = Column(String(100), nullable=False)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id))

    viewers = relationship('QueryViewer', secondary=query_viewers)
    model_version = relationship('ModelVersion')
    tags = relationship('Tag', secondary=query_tags)
    executions = relationship('QueryExecution')


class QueryExecution(Base):
    __tablename__ = 'query_executions'

    id = Column(BigInteger, nullable=False, unique=True, index=True, autoincrement=True, primary_key=True)
    guid = Column(String(100), nullable=False, unique=True, index=True)

    query_id = Column(BigInteger, ForeignKey(Query.id, ondelete='CASCADE'), nullable=False)
    query_run_id = Column(BigInteger, nullable=True)
    status = Column(String(20), nullable=False)

    status_updated_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    publish_name = Column(String(500), nullable=True)
    publish_status = Column(String(20), nullable=True)

    query = relationship('Query')
