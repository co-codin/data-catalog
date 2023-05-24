from app.database import Base
from sqlalchemy import Column, BigInteger, String, DateTime, Text
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB


class Log(Base):
    __tablename__ = 'logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    type = Column(String(36), nullable=False, index=True)
    log_name = Column(String(36), nullable=False, index=True)
    text = Column(Text, nullable=False)
    identity_id = Column(String(36), nullable=False, index=True)
    event = Column(String(36), nullable=False)
    description = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    properties = Column(JSONB, nullable=True)
