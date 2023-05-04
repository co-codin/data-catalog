from app.database import Base
from sqlalchemy import Column, BigInteger, String, DateTime, Text
from datetime import datetime
from sqlalchemy.sql import func


class ActivityLog(Base):
    __tablename__ = 'activity_log'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    type = Column(String(36), nullable=False, index=True)
    action = Column(String(36), nullable=False, index=True)
    description = Column(Text, nullable=False)
    identity_id = Column(String(36), nullable=False)
