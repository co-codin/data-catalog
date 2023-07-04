from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base
from app.models.sources import SourceRegister, Object, Field
from app.models.models import Model, ModelVersion, ModelResource, ModelQuality, Pipeline


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    author_guid = Column(String(36), nullable=False)
    msg = Column(String(10_000), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    source_guid = Column(String(36), ForeignKey(SourceRegister.guid, ondelete='CASCADE'))
    object_guid = Column(String(36), ForeignKey(Object.guid, ondelete='CASCADE'))
    model_guid = Column(String(36), ForeignKey(Model.guid, ondelete='CASCADE'))
    model_version_guid = Column(String(36), ForeignKey(ModelVersion.guid, ondelete='CASCADE'))
    field_guid = Column(String(36), ForeignKey(Field.guid, ondelete='CASCADE'))
    resource_guid = Column(String(36), ForeignKey(ModelResource.guid, ondelete='CASCADE'))
    quality_guid = Column(String(36), ForeignKey(ModelQuality.guid, ondelete='CASCADE'))
    pipeline_guid = Column(String(36), ForeignKey(Pipeline.guid, ondelete='CASCADE'))
