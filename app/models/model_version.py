from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from app.database import Base
from app.models.model import Model
from sqlalchemy.orm import relationship


class ModelVersion(Base):
    __tablename__ = 'model_versions'

    model_id = Column(BigInteger, ForeignKey(Model.id))

    name = Column(String(100), nullable=False)
    owner = Column(String(36*4), nullable=False)
    status = Column(String, nullable=False, default='draft')
    desc = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())
    confirmed_at = Column(DateTime, nullable=True)

    model = relationship('Model', back_populates='model_versions')