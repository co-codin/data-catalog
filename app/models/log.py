from enum import Enum

from app.database import Base
from sqlalchemy import Column, BigInteger, String, DateTime, Text
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB


class LogType(Enum):
    DATA_CATALOG = 'Каталог данных'
    SOURCE_REGISTRY = 'Реестр источников'
    QUERY_CONSTRUCTOR = 'Конструктор запросов'
    OPERATION_REGISTRY = 'Реестр операций'
    MODEL_CATALOG = 'Каталог моделей'


class LogText(Enum):
    CREATE = '{name} {guid} был добавлен с {source_name} {source_guid}'
    EDIT = '{name} {guid} был изменён на {new_name} {new_guid}'
    REMOVE = '{name} {guid} был удалён с {source_name} {source_guid}'
    SYNC_ERROR = 'При синхронизации {name} {guid} произошла ошибка'
    SYNC_SUCCESS = 'Синхронизация {name} {guid} успешно завершена...'
    MODEL_VERSION_CONFIRM = '{version} {guid} в {model_name} {model_guid} утверждена'


class LogEvent(Enum):
    REMOVE = 'Объект был удален с источника'

    CHANGE_OBJECT_TO_SOURCE = 'Изменение объекта на источнике'
    DELETE_OBJECT_FROM_SOURCE = 'Удаление объекта на источнике'
    ADD_OBJECT_TO_SOURCE = 'Добавление объекта на источнике'

    ADD_OBJECT = 'Добавление объекта'
    ADD_OBJECT_FAILED = 'Добавление объекта не удалось'

    SYNC_OBJECT = 'Синхронизация объекта'
    SYNC_OBJECT_FAILED = 'Синхронизация объекта не удалась'

    ADD_SOURCE = 'Добавление источника'
    ADD_SOURCE_FAILED = 'Добавление источника не удалось'

    SYNC_SOURCE = 'Синхронизация источника'
    SYNC_SOURCE_FAILED = 'Синхронизация источника не удалась'

    CONFIRM_VERSION = 'Утверждение версии'
    DELETE_MODEL = 'Удаление модели'




class Log(Base):
    __tablename__ = 'logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    type = Column(String(36), nullable=False, index=True)
    log_name = Column(String(36), nullable=False, index=True)
    description = Column(Text, nullable=True)
    text = Column(Text, nullable=False)
    identity_id = Column(String(36), nullable=False, index=True)
    event = Column(String(36), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    properties = Column(JSONB, nullable=True)
