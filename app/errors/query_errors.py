from fastapi import status

from app.errors import APIError


class QueryNameAlreadyExist(APIError):
    def __init__(self, name: str):
        self.status_code = status.HTTP_409_CONFLICT
        self._name = name

    def __str__(self):
        return f'query {self._name} already exists'


class QueryIsRunningError(APIError):
    def __init__(self):
        self.status_code = status.HTTP_400_BAD_REQUEST

    def __str__(self):
        return 'query is running'


class QueryIsNotRunningError(APIError):
    def __init__(self):
        self.status_code = status.HTTP_400_BAD_REQUEST

    def __str__(self):
        return 'query is not running'
