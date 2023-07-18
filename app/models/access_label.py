from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models import model_resource_attribute_access_labels, model_resource_access_labels, \
    model_version_access_labels, model_access_labels, OperationBody


class AccessLabel(Base):
    __tablename__ = 'access_labels'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    type = Column(String(15), nullable=True)
    operation_version_id = Column(BigInteger, ForeignKey(OperationBody.operation_body_id), nullable=True)

    models = relationship('Model', secondary=model_access_labels)
    model_versions = relationship('ModelVersion', secondary=model_version_access_labels)
    model_resources = relationship('ModelResource', secondary=model_resource_access_labels)
    model_resource_attributes = relationship('ModelResourceAttribute', secondary=model_resource_attribute_access_labels)
    operation_bodies = relationship('OperationBody', back_populates='access_labels')
