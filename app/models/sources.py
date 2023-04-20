import enum

from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum
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


class SourceRegister(Base):
    __tablename__ = 'source_registers'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(100), index=True, unique=True, nullable=False)
    type = Column(String(36), nullable=False)
    origin = Column(Enum(Origin), nullable=False)
    status = Column(Enum(Status), nullable=False)

    conn_string = Column(String(500), unique=True, nullable=False)
    working_mode = Column(Enum(WorkingMode), nullable=False)
    owner = Column(String(36), nullable=False)
    desc = Column(String(500), index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())
    synchronized_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    tags = relationship('Tag')
    comments = relationship('Comment')


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), index=True, unique=True, nullable=False)

    source_guid = Column(String(36), ForeignKey(SourceRegister.guid))


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    author_guid = Column(String(36), nullable=False)
    msg = Column(String(10_000), index=True, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    source_guid = Column(String(36), ForeignKey(SourceRegister.guid))
