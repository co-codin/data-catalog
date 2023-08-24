from fastapi import status

from app.errors import APIError


class QueryExecPublishNameAlreadyExist(APIError):
    def __init__(self, publish_name: str):
        self.status_code = status.HTTP_409_CONFLICT
        self._publish_name = publish_name

    def __str__(self):
        return f'table {self._publish_name} already exist'
