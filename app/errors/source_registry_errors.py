from fastapi import status

from app.errors import APIError
from app.models import Status


class SourceRegistryIsNotOnError(APIError):
    def __init__(self, status_: Status):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._status = status_

    def __str__(self):
        return f'Source registry status is {self._status.value}, must be on'


class SourceRegistryNameAlreadyExist(APIError):
    def __init__(self, name: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._name = name

    def __str__(self):
        return f'source registry name {self._name} already exists'


class ConnStringAlreadyExist(APIError):
    def __init__(self, conn_string: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._conn_string = conn_string

    def __str__(self):
        return f'conn_string {self._conn_string} already exists'
