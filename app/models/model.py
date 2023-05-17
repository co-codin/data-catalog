from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum, Table, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Model(Base):
    pass