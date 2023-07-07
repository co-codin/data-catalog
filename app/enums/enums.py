from enum import Enum


class ModelVersionLevel(Enum):
    CRITICAL = 'critical'
    MINOR = 'minor'
    PATCH = 'patch'


class ModelVersionStatus(Enum):
    APPROVED = 'approved'
    ARCHIVE = 'archive'
    DRAFT = 'draft'

