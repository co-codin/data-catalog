from enum import Enum
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.database.sqlalchemy import Base


class LogType(Enum):
    DATA_CATALOG = 'Каталог данных'
    SOURCE_REGISTRY = 'Реестр источников'
    QUERY_CONSTRUCTOR = 'Конструктор запросов'
    OPERATION_REGISTRY = 'Реестр операций'
    MODEL_CATALOG = 'Каталог моделей'


class LogName(Enum):
    SOURCE_ADD = 'Добавление источника'
    OBJECT_ADD = 'Добавление объекта'

    OBJECT_ALTER = 'Изменение объекта на источнике'

    SOURCE_SYNC = 'Синхронизация источника'
    OBJECT_SYNC = 'Синхронизация объекта'

    MODEL_VERSION_CONFIRM = 'Утверждение версии'

    QUERY_RUN = 'Запуск запроса'
    QUERY_CANCEL = 'Остановка запроса'
    QUERY_RESULT = 'Результат запроса получен'
    QUERY_ERROR = 'Ошибка в результате запуска запроса'


class LogText(Enum):
    CREATE = '{name} был добавлен с {source_name} {source_guid}'
    ALTER = '{name} был изменён на {new_name}'
    REMOVE = '{name} {guid} был удалён с {source_name} {source_guid}'
    SYNC_ERROR = 'При синхронизации {{{{{name}}}}} произошла ошибка'
    SYNC_SUCCESS = "Синхронизация {{{{{name}}}}} успешно завершена. Добавлено - {added} объектов. Изменено - {altered}. Удалено - {deleted}. Объектов без изменений - {not_changed}"

    MODEL_VERSION_CONFIRM = '{{{{{model_version}}}}} в {{{{{model_name}}}}} утверждена'

    QUERY_RUN = "Запрос {{{{{name}}}}} был запущен"
    QUERY_RUN_SUCCESS = "Результат запроса {{{{{name}}}}} получен"
    QUERY_RUN_ERROR = "Запуск запроса {{{{{name}}}}} был завершен с ошибкой"
    QUERY_RUN_CANCEL = "Запрос {{{{{name}}}}} был остановлен"


class LogEvent(Enum):
    REMOVE = 'Объект был удален с источника'

    CHANGE_OBJECT_TO_SOURCE = 'Изменение объекта на источнике'
    DELETE_OBJECT_FROM_SOURCE = 'Удаление объекта на источнике'
    ADD_OBJECT_TO_SOURCE = 'Добавление объекта вручную из подключенного источника'

    ADD_OBJECT = 'Добавление объекта'
    ADD_OBJECT_FAILED = 'Добавление объекта не удалось'

    SYNC_OBJECT = 'Синхронизация объекта'
    SYNC_OBJECT_FAILED = 'Синхронизация объекта не удалась'

    ADD_SOURCE = 'Добавление источника'
    ADD_SOURCE_FAILED = 'Добавление источника не удалось'

    SYNC_SOURCE_AUTO = 'Синхронизация при добавлении источника'
    SYNC_SOURCE_MANUAL = 'Синхронизация из Реестра источников'
    SYNC_SOURCE_FAIL = 'Синхронизация источника не удалась'

    CONFIRM_VERSION = 'Утверждение версии'
    DELETE_MODEL = 'Удаление модели'

    RUN_QUERY_REQUEST = 'Запрос был запущен на выполнение'
    RUN_QUERY_SUCCESS = 'Запуск запроса завершен'
    RUN_QUERY_FAILED = 'Запуск запроса завершен с ошибкой'
    RUN_QUERY_CANCEL = 'Запрос был остановлен'


class Log(Base):
    __tablename__ = 'logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    type = Column(String(36), nullable=False, index=True)
    log_name = Column(Text, nullable=False, index=True)
    description = Column(Text, nullable=True)
    text = Column(Text, nullable=False)
    identity_id = Column(String(36), nullable=False, index=True)
    event = Column(String(100), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    properties = Column(JSONB, nullable=True)
