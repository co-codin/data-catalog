from starlette import status

from app.errors import APIError


class ModelVersionStatusError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Model version must be approved or achieved"


class PipelineNameNotUniqueError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Pipeline with this name or parameter set already exists"
