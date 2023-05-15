from app.database import Base
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB


class ActivityLog(Base):
    __tablename__ = 'activity_log'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    log_name = Column(String(36), nullable=False, index=True)
    description = Column(Text, nullable=False)

    subject_type = Column(String(36), nullable=False)
    subject_id = Column(BigInteger, nullable=False, index=True)

    identity_id = Column(String(36), nullable=False, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    type = Column(String(36), nullable=False, index=True)

    properties = Column(JSONB, nullable=True)