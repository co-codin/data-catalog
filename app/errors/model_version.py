from fastapi import status

from app.errors import APIError


class ModelVersionNotDraftError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Model version isn't in draft status"


class ModelVersionDBLinkError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = 461
        self._nodes = nodes

    def __str__(self):
        return "Model version contains resource with corrupted db_link"


class ModelVersionEmptyResourceError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = 462
        self._nodes = nodes

    def __str__(self):
        return "Model version contains resource without attributes"


class ModelVersionDataTypeError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = 463
        self._nodes = nodes

    def __str__(self):
        return "Model version contains resource with attribute without type"


class ModelVersionNestedAttributeDataTypeError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = 464
        self._nodes = nodes

    def __str__(self):
        return "Model version contains resource with nested attribute with wrong type"


class ModelVersionAttributeDBLinkError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = 465
        self._nodes = nodes

    def __str__(self):
        return "Model version contains resource with nested attribute with empty db_link"
