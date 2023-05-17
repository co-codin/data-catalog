from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

model_tags = Table(
    "model_tags",
    Base.metadata,
    Column("model_tags", ForeignKey("models.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

class Model(Base):
    __tablename__ = 'models'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    owner = Column(String(36*4), nullable=False)
    desc = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    tags = relationship('Tag', secondary=model_tags, order_by='Tag.id')


