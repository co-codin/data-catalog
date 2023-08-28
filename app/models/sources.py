import enum

from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum, Table, Text, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.sqlalchemy import Base


class Origin(enum.Enum):
    INTERNAL = 'internal'
    PRIMARY = 'primary'


class WorkingMode(enum.Enum):
    PASSIVE = 'passive'
    ACTIVE = 'active'
    BATCHED = 'batched'
    STREAMED = 'streamed'


class Status(enum.Enum):
    ON = 'on'
    OFF = 'off'
    SYNCHRONIZING = 'synchronizing'


source_registry_tags = Table(
    "source_registry_tags",
    Base.metadata,
    Column("source_registry_id", ForeignKey("source_registers.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

objects_tags = Table(
    "objects_tags",
    Base.metadata,
    Column("object_id", ForeignKey("objects.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

fields_tags = Table(
    "fields_tags",
    Base.metadata,
    Column("field_id", ForeignKey("fields.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_tags = Table(
    "model_tags",
    Base.metadata,
    Column("model_tags", ForeignKey("models.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

model_access_labels = Table(
    "model_access_labels",
    Base.metadata,
    Column("model_access_labels", ForeignKey("models.id", ondelete='CASCADE'),
           primary_key=True),
    Column("access_label_id", ForeignKey("access_labels.id"), primary_key=True)
)


class SourceRegister(Base):
    __tablename__ = 'source_registers'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)

    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(36), nullable=False)
    origin = Column(Enum(Origin), nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.SYNCHRONIZING)

    conn_string = Column(String(728), nullable=False)
    working_mode = Column(Enum(WorkingMode), nullable=False)
    owner = Column(String(36*4), nullable=False)
    desc = Column(String(500))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    synchronized_at = Column(DateTime)

    models = relationship('Model')
    tags = relationship('Tag', secondary=source_registry_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    objects = relationship('Object')

    @property
    def objects_set(self):
        return {object_.name for object_ in self.objects}

    def object_db_path_to_object(self, tables: set[str]):
        return {object_.db_path: object_ for object_ in self.objects if object_.db_path in tables}


class Object(Base):
    __tablename__ = 'objects'

    id = Column(BigInteger, nullable=False, autoincrement=True, primary_key=True)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)
    owner = Column(String(36*4), nullable=False)
    db_path = Column(String, index=True)

    source_created_at = Column(DateTime)
    source_updated_at = Column(DateTime)
    local_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    synchronized_at = Column(DateTime)

    short_desc = Column(Text)
    business_desc = Column(Text)

    is_synchronizing = Column(Boolean, nullable=False, default=False)

    source_registry_guid = Column(String(36), ForeignKey(SourceRegister.guid))

    fields = relationship('Field')
    tags = relationship('Tag', secondary=objects_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')
    source = relationship('SourceRegister')

    @property
    def field_db_path_to_field(self):
        return {field.db_path: field for field in self.fields}


class Field(Base):
    __tablename__ = 'fields'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    object_guid = Column(String, ForeignKey(Object.guid, ondelete='CASCADE'))

    name = Column(String, nullable=False)
    data_type_id = Column(BigInteger, index=True, nullable=True)

    length = Column(Integer, nullable=False)
    is_key = Column(Boolean, nullable=False)
    db_path = Column(String, nullable=False)
    owner = Column(String(36*4), nullable=False)
    desc = Column(Text)

    source_created_at = Column(DateTime)
    source_updated_at = Column(DateTime)
    local_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    synchronized_at = Column(DateTime)

    object = relationship('Object')
    tags = relationship('Tag', secondary=fields_tags, order_by='Tag.id')
    comments = relationship('Comment', order_by='Comment.id')


class Model(Base):
    __tablename__ = 'models'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guid = Column(String(36), nullable=False, index=True, unique=True)
    source_registry_id = Column(BigInteger, ForeignKey(SourceRegister.id, ondelete='CASCADE'))

    name = Column(String(100), nullable=False)
    owner = Column(String(36*4), nullable=False)
    short_desc = Column(Text)
    business_desc = Column(Text)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow,
                        server_onupdate=func.now())

    tags = relationship('Tag', secondary=model_tags, order_by='Tag.id')
    access_label = relationship('AccessLabel', secondary=model_access_labels, order_by='AccessLabel.id')
    model_versions = relationship('ModelVersion', back_populates='model')
    comments = relationship('Comment', order_by='Comment.id')
    deleted_at = Column(DateTime, nullable=True)
