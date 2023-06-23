from enum import Enum

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base
from app.models.models import ModelVersion, ModelResourceAttribute


class QueryStatus(Enum):
    CREATED = 0
    PROCESSING = 1
    FINISHED = 2
    STOPPED = 3
    FAULT = 4


query_constructor_tags = Table(
    "query_constructor_tags",
    Base.metadata,
    Column("id", ForeignKey("query_constructors.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


class QueryConstructor(Base):
    __tablename__ = 'query_constructors'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(200), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(String(1000), nullable=True)
    status = Column(Integer, nullable=False, default=QueryStatus.CREATED.value)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    tags = relationship('Tag', secondary=query_constructor_tags, order_by='Tag.id')
    query_constructor_body = relationship('QueryConstructorBody', back_populates='query_constructor')
    query_constructor_reviewer = relationship('QueryConstructorReviewer', back_populates='query_constructor')
    query_constructor_history = relationship('QueryConstructorHistory', back_populates='query_constructor')


class QueryConstructorBody(Base):
    __tablename__ = 'query_constructor_bodies'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    query_constructor_id = Column(BigInteger, ForeignKey(QueryConstructor.id, ondelete='CASCADE'))
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id, ondelete='CASCADE'))

    filters = Column(JSONB, nullable=True)
    aggregators = Column(JSONB, nullable=True)

    query_constructor = relationship('QueryConstructor', back_populates='query_constructor_body')
    query_constructor_body_field = relationship('QueryConstructorBodyField', back_populates='query_constructor_body')
    model_version = relationship('ModelVersion', back_populates='query_constructor_body')


class QueryConstructorBodyField(Base):
    __tablename__ = 'query_constructor_body_fields'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_resource_attribute_id = Column(BigInteger, ForeignKey(ModelResourceAttribute.id, ondelete='CASCADE'))
    query_constructor_body_id = Column(BigInteger, ForeignKey(QueryConstructorBody.id, ondelete='CASCADE'))

    query_constructor_body = relationship('QueryConstructorBody', back_populates='query_constructor_body_field')
    model_resource_attribute = relationship('ModelResourceAttribute', back_populates='query_constructor_body_field')


class QueryConstructorReviewer(Base):
    __tablename__ = 'query_constructor_reviewers'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    query_constructor_id = Column(BigInteger, ForeignKey(QueryConstructor.id, ondelete='CASCADE'))
    name = Column(String(100), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    query_constructor = relationship('QueryConstructor', back_populates='query_constructor_reviewer')


class QueryConstructorHistory(Base):
    __tablename__ = 'query_constructor_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    query_constructor_id = Column(BigInteger, ForeignKey(QueryConstructor.id, ondelete='CASCADE'))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    ended_at = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=False, default=QueryStatus.PROCESSING.value)

    query_constructor = relationship('QueryConstructor', back_populates='query_constructor_history')
