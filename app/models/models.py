from datetime import datetime
from enum import Enum

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table, Text, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base
from app.models.sources import Model


class Cardinality(Enum):
    ZERO_TO_ONE = '0..1'
    ZERO_TO_MANY = '0..*'
    ONE_TO_ONE = '1..1'
    ONE_TO_MANY = '1..*'


model_version_tags = Table(
    "model_version_tags",
    Base.metadata,
    Column("model_version_tags", ForeignKey("model_versions.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_quality_tags = Table(
    "model_quality_tags",
    Base.metadata,
    Column("model_quality_tags", ForeignKey("model_qualities.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_relation_group_tags = Table(
    "model_relation_group_tags",
    Base.metadata,
    Column("model_relation_group_tags", ForeignKey("model_relation_groups.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_relation_tags = Table(
    "model_relation_tags",
    Base.metadata,
    Column("model_relation_tags", ForeignKey("model_relations.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_resource_tags = Table(
    "model_resource_tags",
    Base.metadata,
    Column("model_resource_tags", ForeignKey("model_resources.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_resource_attribute_tags = Table(
    "model_resource_attribute_tags",
    Base.metadata,
    Column("model_resource_attribute_tags", ForeignKey("model_resource_attributes.id", ondelete='CASCADE'),
           primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


class ModelVersion(Base):
    __tablename__ = 'model_versions'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    guid = Column(String(36), nullable=False, index=True, unique=True)

    model_id = Column(BigInteger, ForeignKey(Model.id, ondelete='CASCADE'))
    status = Column(String, nullable=False, default='draft')
    version = Column(String(100), nullable=True)
    owner = Column(String(36 * 4), nullable=False)

    desc = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())
    model = relationship('Model', back_populates='model_versions')

    tags = relationship('Tag', secondary=model_version_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    model_qualities = relationship('ModelQuality', back_populates='model_version')
    relation_groups = relationship('ModelRelationGroup', back_populates='model_version')
    model_resources = relationship('ModelResource', back_populates='model_version')
    confirmed_at = Column(DateTime, nullable=True)


class ModelDataType(Base):
    __tablename__ = 'model_data_types'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), nullable=False)
    desc = Column(Text, nullable=True)

    json = Column(JSONB, nullable=True)
    xml = Column(Text, nullable=True)


class ModelQuality(Base):
    __tablename__ = 'model_qualities'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id))

    name = Column(String(200), nullable=False)
    owner = Column(String(36 * 4), nullable=False)

    desc = Column(Text, nullable=True)
    function = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_version = relationship('ModelVersion', back_populates='model_qualities')
    tags = relationship('Tag', secondary=model_quality_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')


class ModelRelationGroup(Base):
    __tablename__ = 'model_relation_groups'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id))

    name = Column(String(100), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_version = relationship('ModelVersion', back_populates='relation_groups')
    model_relations = relationship('ModelRelation', back_populates='model_relation_group')
    tags = relationship('Tag', secondary=model_relation_group_tags, order_by='Tag.id')


class ModelRelation(Base):
    __tablename__ = 'model_relations'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_relation_group_id = Column(BigInteger, ForeignKey(ModelRelationGroup.id))

    name = Column(String(100), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(String(500))
    function = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_relation_group = relationship('ModelRelationGroup', back_populates='model_relations')
    tags = relationship('Tag', secondary=model_relation_tags, order_by='Tag.id')


class ModelResource(Base):
    __tablename__ = 'model_resources'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id))

    name = Column(String(100), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(String(500))
    type = Column(String(500))
    db_link = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_version = relationship('ModelVersion', back_populates='model_resources')
    model_attitudes = relationship('ModelAttitude', back_populates='model_resources')
    attributes = relationship('ModelResourceAttribute', back_populates='model_resources')
    tags = relationship('Tag', secondary=model_resource_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')


class ModelAttitude(Base):
    __tablename__ = 'model_attitudes'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    resource_id = Column(BigInteger, ForeignKey(ModelResource.id))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_resources = relationship('ModelResource', back_populates='model_attitudes')


class ModelResourceAttribute(Base):
    __tablename__ = 'model_resource_attributes'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    resource_id = Column(BigInteger, ForeignKey(ModelResource.id))

    name = Column(String(100), nullable=False)
    key = Column(Boolean, index=True, nullable=True)
    db_link = Column(String(500))
    desc = Column(String(1000))

    data_type_id = Column(BigInteger, index=True, nullable=True)
    data_type_flag = Column(Integer, nullable=True)

    cardinality = Column(String(100), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_resources = relationship('ModelResource', back_populates='attributes')
    tags = relationship('Tag', secondary=model_resource_attribute_tags, order_by='Tag.id')

    parent_id = Column(BigInteger, nullable=True)
    additional = Column(JSONB, nullable=True)
