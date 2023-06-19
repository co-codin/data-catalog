from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base
from app.models.models import ModelDataType

operation_tags = Table(
    "operation_tags",
    Base.metadata,
    Column("operation_id", ForeignKey("operations.operation_id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


class Operation(Base):
    __tablename__ = 'operations'

    operation_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(200), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    status = Column(String(50), nullable=False)
    desc = Column(String(1000), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    tags = relationship('Tag', secondary=operation_tags, order_by='Tag.id')
    operation_body = relationship('OperationBody', back_populates='operation')


class OperationBody(Base):
    __tablename__ = 'operation_bodies'

    operation_body_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    code = Column(Text, nullable=False)
    operation_body_parameters = relationship('OperationBodyParameter', back_populates='operation_body')
    operation = relationship('Operation', back_populates='operation_body')
    operation_id = Column(BigInteger, ForeignKey(Operation.operation_id, ondelete='CASCADE'))


class OperationBodyParameter(Base):
    __tablename__ = 'operation_body_parameters'

    operation_body_parameter_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    operation_body_id = Column(BigInteger, ForeignKey(OperationBody.operation_body_id, ondelete='CASCADE'))

    flag = Column(Boolean, unique=False, default=True)
    name = Column(String(200), nullable=False)
    name_for_relation = Column(String(200), nullable=False)
    model_data_type_id = Column(BigInteger, ForeignKey(ModelDataType.id))
    operation_body = relationship('OperationBody', back_populates='operation_body_parameters')
