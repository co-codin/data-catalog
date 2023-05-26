from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

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
    confirmed_at = Column(DateTime, nullable=True)

    model = relationship('Model', back_populates='model_versions')

    tags = relationship('Tag', secondary=model_version_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')