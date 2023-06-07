from fastapi import status

from app.errors import APIError


class ModelQualityErrorAlreadyExist(APIError):
    def __init__(self, name: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._name = name

    def __str__(self):
        return f'model quality {self._name} already exists'
