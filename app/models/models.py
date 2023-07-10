from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Table, Text, Boolean, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base
from app.enums.enums import ModelVersionStatus, PipelineStatus
from app.models.sources import Model


model_version_tags = Table(
    "model_version_tags",
    Base.metadata,
    Column("model_version_tags", ForeignKey("model_versions.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_quality_tags = Table(
    "model_quality_tags",
    Base.metadata,
    Column("model_quality_tags", ForeignKey("model_qualities.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_relation_tags = Table(
    "model_relation_tags",
    Base.metadata,
    Column("model_relation_tags", ForeignKey("model_relations.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_resource_tags = Table(
    "model_resource_tags",
    Base.metadata,
    Column("model_resource_tags", ForeignKey("model_resources.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_resource_attribute_tags = Table(
    "model_resource_attribute_tags",
    Base.metadata,
    Column("model_resource_attribute_tags", ForeignKey("model_resource_attributes.id", ondelete='CASCADE'),
           primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

operation_tags = Table(
    "operation_tags",
    Base.metadata,
    Column("operation_id", ForeignKey("operations.operation_id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

pipeline_tags = Table(
    "pipeline_tags",
    Base.metadata,
    Column("pipeline_id", ForeignKey("pipelines.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


class ModelDataType(Base):
    __tablename__ = 'model_data_types'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), nullable=False)
    desc = Column(Text, nullable=True)

    json = Column(JSONB, nullable=True)
    xml = Column(Text, nullable=True)

    model_resource_attributes = relationship('ModelResourceAttribute', back_populates='model_data_types')


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

    operation_id = Column(BigInteger, ForeignKey(Operation.operation_id, ondelete='CASCADE'))
    operation_body_id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    version = Column(BigInteger, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    version_owner = Column(String(36 * 4), nullable=True)
    version_desc = Column(String(1000), nullable=True)

    code = Column(Text, nullable=False)
    operation_body_parameters = relationship('OperationBodyParameter', back_populates='operation_body')
    operation = relationship('Operation', back_populates='operation_body')
    model_relation_operations = relationship('ModelRelationOperation', back_populates='operations_bodies')


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


class ModelVersion(Base):
    __tablename__ = 'model_versions'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    model_id = Column(BigInteger, ForeignKey(Model.id, ondelete='CASCADE'))
    status = Column(String, nullable=False, default=ModelVersionStatus.DRAFT.value)
    version = Column(String(100), nullable=True)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(Text)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())
    confirmed_at = Column(DateTime, nullable=True)

    model = relationship('Model', back_populates='model_versions')
    tags = relationship('Tag', secondary=model_version_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    model_qualities = relationship('ModelQuality', back_populates='model_version')
    model_relations = relationship('ModelRelation', back_populates='model_version')
    model_resources = relationship('ModelResource', back_populates='model_version')
    query_constructor_body = relationship('QueryConstructorBody', back_populates='model_version')


class ModelQuality(Base):
    __tablename__ = 'model_qualities'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id, ondelete='CASCADE'))

    name = Column(String(200), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(Text, nullable=True)
    function = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_version = relationship('ModelVersion', back_populates='model_qualities')
    tags = relationship('Tag', secondary=model_quality_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')


class ModelRelation(Base):
    __tablename__ = 'model_relations'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id, ondelete='CASCADE'))

    name = Column(String(200), nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_version = relationship('ModelVersion', back_populates='model_relations')
    tags = relationship('Tag', secondary=model_relation_tags, order_by='Tag.id')
    relation_operation = relationship('ModelRelationOperation', back_populates='model_relation')


class ModelRelationOperation(Base):
    __tablename__ = 'model_relation_operations'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_relation_id = Column(BigInteger, ForeignKey(ModelRelation.id, ondelete='CASCADE'), nullable=True)
    operation_body_id = Column(BigInteger, ForeignKey(OperationBody.operation_body_id, ondelete='CASCADE'))
    parent_id = Column(BigInteger, nullable=True)

    model_relation = relationship('ModelRelation', back_populates='relation_operation')
    operations_bodies = relationship('OperationBody', back_populates='model_relation_operations')
    model_relation_operations = relationship('ModelRelationOperationParameter',
                                             back_populates='model_relation_operation')


class ModelRelationOperationParameter(Base):
    __tablename__ = 'model_relation_operation_parameters'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_relation_operation_id = Column(BigInteger, ForeignKey(ModelRelationOperation.id, ondelete='CASCADE'))

    model_resource_attribute_id = Column(BigInteger, ForeignKey('model_resource_attributes.id'), nullable=True)
    value = Column(JSONB, nullable=True)

    model_resource_attributes = relationship('ModelResourceAttribute',
                                             back_populates='model_relation_operation_parameters')
    model_relation_operation = relationship('ModelRelationOperation', back_populates='model_relation_operations')


class ModelResource(Base):
    __tablename__ = 'model_resources'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id, ondelete='CASCADE'))

    name = Column(Text, nullable=False)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(Text, nullable=True)
    type = Column(String(500), default="Ресурс")
    db_link = Column(String(500), nullable=True, index=True)

    json = Column(JSONB, nullable=True)
    xml = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_version = relationship('ModelVersion', back_populates='model_resources')
    model_attitudes = relationship('ModelAttitude', back_populates='model_resources')
    attributes = relationship('ModelResourceAttribute', primaryjoin='ModelResource.id==ModelResourceAttribute'
                                                                    '.resource_id',
                              order_by='ModelResourceAttribute.name')
    typed_attributes = relationship('ModelResourceAttribute', primaryjoin='ModelResource.id==ModelResourceAttribute'
                                                                          '.model_resource_id')
    tags = relationship('Tag', secondary=model_resource_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')


class ModelResourceAttribute(Base):
    __tablename__ = 'model_resource_attributes'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(200), nullable=False)
    key = Column(Boolean, index=True, nullable=True)
    db_link = Column(String(500), nullable=True, index=True)
    desc = Column(Text, nullable=True)
    cardinality = Column(String(100), nullable=True)
    parent_id = Column(BigInteger, nullable=True, index=True)
    additional = Column(JSONB, nullable=True)

    resource_id = Column(BigInteger, ForeignKey(ModelResource.id, ondelete='CASCADE'))
    model_resource_id = Column(BigInteger, ForeignKey(ModelResource.id), nullable=True)
    model_data_type_id = Column(BigInteger, ForeignKey(ModelDataType.id, ondelete='CASCADE'), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    resources = relationship('ModelResource', back_populates='attributes', foreign_keys=[resource_id])
    model_resources = relationship('ModelResource', back_populates='typed_attributes', foreign_keys=[model_resource_id])
    model_data_types = relationship('ModelDataType', back_populates='model_resource_attributes')
    tags = relationship('Tag', secondary=model_resource_attribute_tags, order_by='Tag.id')
    query_constructor_body_field = relationship('QueryConstructorBodyField', back_populates='model_resource_attribute')

    left_attribute_attitudes = relationship('ModelAttitude', primaryjoin='ModelResourceAttribute.id==ModelAttitude'
                                                                         '.left_attribute_id')
    right_attribute_attitudes = relationship('ModelAttitude', primaryjoin='ModelResourceAttribute.id==ModelAttitude'
                                                                          '.right_attribute_id')
    model_relation_operation_parameters = relationship('ModelRelationOperationParameter',
                                                       back_populates='model_resource_attributes')


class ModelAttitude(Base):
    __tablename__ = 'model_attitudes'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    resource_id = Column(BigInteger, ForeignKey(ModelResource.id, ondelete='CASCADE'))
    left_attribute_id = Column(BigInteger, ForeignKey(ModelResourceAttribute.id, ondelete='CASCADE'))
    right_attribute_id = Column(BigInteger, ForeignKey(ModelResourceAttribute.id, ondelete='CASCADE'))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    model_resources = relationship('ModelResource', back_populates='model_attitudes')
    left_attributes = relationship('ModelResourceAttribute', back_populates='left_attribute_attitudes',
                                   foreign_keys=[left_attribute_id])
    right_attributes = relationship('ModelResourceAttribute', back_populates='right_attribute_attitudes',
                                    foreign_keys=[right_attribute_id])


class Pipeline(Base):
    __tablename__ = 'pipelines'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(500), nullable=False, index=True, unique=True)
    owner = Column(String(36 * 4), nullable=False)
    desc = Column(String(1000), nullable=True)
    model_version_id = Column(BigInteger, ForeignKey(ModelVersion.id, ondelete='CASCADE'))
    state = Column(Boolean(), nullable=False, default=True)
    base = Column(Boolean(), nullable=False, default=True)
    operating_mode = Column(Boolean(), nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    tags = relationship('Tag', secondary=pipeline_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    pipeline_result = relationship('PipelineResult', back_populates='pipeline')


class PipelineResult(Base):
    __tablename__ = 'pipeline_results'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    pipeline_id = Column(BigInteger, ForeignKey(Pipeline.id, ondelete='CASCADE'))

    status = Column(BigInteger(), nullable=False, default=PipelineStatus.EXPECTED.value)
    attachment = Column(LargeBinary(), nullable=True)

    pipeline = relationship('Pipeline', back_populates='pipeline_result')
