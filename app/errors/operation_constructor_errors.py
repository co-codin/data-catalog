from starlette import status

from app.errors import APIError


class QueryConstructorWrongOwnerExists(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_403_FORBIDDEN
        self._nodes = nodes

    def __str__(self):
        return "Impossible access to Query if you isn't its owner"


class QueryAlreadyRunError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Query is already run"


class QueryIsRunError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Query is processing and can't be changed"


class QueryAlreadyStoppedError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Query is already stopped"
