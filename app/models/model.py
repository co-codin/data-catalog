from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

model_tags = Table(
    "model_tags",
    Base.metadata,
    Column("model_tags", ForeignKey("models.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

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

class Model(Base):
    __tablename__ = 'models'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    name = Column(String(100), nullable=False)
    owner = Column(String(36*4), nullable=False)
    short_desc = Column(Text)
    business_desc = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    tags = relationship('Tag', secondary=model_tags, order_by='Tag.id')
    model_versions = relationship('ModelVersion', back_populates='model')
    comments = relationship('Comment', order_by='Comment.id')


class ModelVersion(Base):
    __tablename__ = 'model_versions'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    guid = Column(String(36), nullable=False, index=True, unique=True)

    model_id = Column(BigInteger, ForeignKey(Model.id))
    status = Column(String, nullable=False, default='draft')
    version = Column(String(100), nullable=True)
    owner = Column(String(36*4), nullable=False)

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
    desc = Column(String(500))

    json = Column(JSONB)
    xml = Column(Text)


class ModelQuality(Base):
    __tablename__ = 'model_qualities'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id))

    name = Column(String(100), nullable=False)
    owner = Column(String(36*4), nullable=False)

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
