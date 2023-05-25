import enum

from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum, Table, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.model import Model, ModelVersion, model_tags, model_version_tags

from app.database import Base


class Origin(enum.Enum):
    INTERNAL = 'internal'
    PRIMARY = 'primary'


class WorkingMode(enum.Enum):
    PASSIVE = 'passive'
    ACTIVE = 'active'
    BATCHED = 'batched'
    STREAMED = 'streamed'


class Status(enum.Enum):
    ON = 'on'
    OFF = 'off'
    SYNCHRONIZING = 'synchronizing'


source_registry_tags = Table(
    "source_registry_tags",
    Base.metadata,
    Column("source_registry_id", ForeignKey("source_registers.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

objects_tags = Table(
    "objects_tags",
    Base.metadata,
    Column("object_id", ForeignKey("objects.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


class SourceRegister(Base):
    __tablename__ = 'source_registers'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(36), nullable=False)
    origin = Column(Enum(Origin), nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.SYNCHRONIZING)

    conn_string = Column(String(728), nullable=False)
    working_mode = Column(Enum(WorkingMode), nullable=False)
    owner = Column(String(36*4), nullable=False)
    desc = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())
    synchronized_at = Column(DateTime)

    tags = relationship('Tag', secondary=source_registry_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    objects = relationship('Object')


class Object(Base):
    __tablename__ = 'objects'

    id = Column(BigInteger, nullable=False, autoincrement=True, primary_key=True)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)
    owner = Column(String(36*4), nullable=False)

    source_created_at = Column(DateTime)
    source_updated_at = Column(DateTime)
    local_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                              server_onupdate=func.now())
    synchronized_at = Column(DateTime)

    short_desc = Column(Text)
    business_desc = Column(Text)

    is_synchronized = Column(Boolean, nullable=False, default=False)

    source_registry_guid = Column(String(36), ForeignKey(SourceRegister.guid))

    tags = relationship('Tag', secondary=objects_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    source = relationship('SourceRegister')


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)

    source_registries = relationship('SourceRegister', secondary=source_registry_tags)
    objects = relationship('Object', secondary=objects_tags)
    models = relationship('Model', secondary=model_tags)
    model_versions = relationship('ModelVersion', secondary=model_version_tags)


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    author_guid = Column(String(36), nullable=False)
    msg = Column(String(10_000), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    source_guid = Column(String(36), ForeignKey(SourceRegister.guid, ondelete='CASCADE'))
    object_guid = Column(String(36), ForeignKey(Object.guid, ondelete='CASCADE'))
    model_guid = Column(String(36), ForeignKey(Model.guid, ondelete='CASCADE'))
    model_version_guid = Column(String(36), ForeignKey(ModelVersion.guid, ondelete='CASCADE'))
