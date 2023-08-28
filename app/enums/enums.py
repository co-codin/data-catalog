from enum import Enum


class ModelVersionLevel(Enum):
    CRITICAL = 'critical'
    MINOR = 'minor'
    PATCH = 'patch'


class ModelVersionStatus(Enum):
    APPROVED = 'approved'
    ARCHIVE = 'archive'
    DRAFT = 'draft'


class Cardinality(Enum):
    ZERO_TO_ONE = '0..1'
    ZERO_TO_MANY = '0..*'
    ONE_TO_ONE = '1..1'
    ONE_TO_MANY = '1..*'


class PipelineStatus(Enum):
    EXPECTED = 0
    ERROR = 1
    SUCCESS = 2


class AccessLabelType(Enum):
    PERSONAL = 'personal'
    CONFIDENTIAL = 'confidential'
    FREE = 'free'


class SyncType(Enum):
    ADD_OBJECT = 1
    SYNC_OBJECT = 2
    ADD_SOURCE = 3
    SYNC_SOURCE = 4
