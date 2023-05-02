import enum

from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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


class SourceRegister(Base):
    __tablename__ = 'source_registers'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(36), nullable=False)
    origin = Column(Enum(Origin), nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.SYNCHRONIZING)

    conn_string = Column(String(500), unique=True, nullable=False)
    working_mode = Column(Enum(WorkingMode), nullable=False)
    owner = Column(String(36*4), nullable=False)
    desc = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())
    synchronized_at = Column(DateTime)

    tags = relationship('Tag', secondary=source_registry_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)

    source_registries = relationship('SourceRegister', secondary=source_registry_tags)


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    author_guid = Column(String(36), nullable=False)
    msg = Column(String(10_000), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    source_guid = Column(String(36), ForeignKey(SourceRegister.guid, ondelete='CASCADE'))
