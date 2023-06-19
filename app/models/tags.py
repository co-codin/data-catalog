from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm import relationship

from app.models.operations import operation_tags
from app.models.sources import source_registry_tags, objects_tags, model_tags, fields_tags
from app.models.models import model_version_tags
from app.database import Base


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)

    source_registries = relationship('SourceRegister', secondary=source_registry_tags)
    objects = relationship('Object', secondary=objects_tags)
    fields = relationship('Field', secondary=fields_tags)
    models = relationship('Model', secondary=model_tags)
    model_versions = relationship('ModelVersion', secondary=model_version_tags)
    operations = relationship('Operation', secondary=operation_tags)
