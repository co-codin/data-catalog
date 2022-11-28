from fastapi import status


class APIError(Exception):
    status_code: int


class NoEntityError(APIError):
    def __init__(self, entity: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._entity = entity

    def __str__(self):
        return f"Entity {self._entity} doesn't exist"


class NoFieldError(APIError):
    def __init__(self, field: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._field = field

    def __str__(self):
        return f"Field {self._field} doesn't exist"


class UnknownRelationTypeError(APIError):
    def __init__(self, relation_type: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._relation_type = relation_type

    def __str__(self):
        return f"Unknown relation {self._relation_type}"


class NoNeo4jConnection(APIError):
    def __init__(self, neo4j_conn_string):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._neo4j_conn_string = neo4j_conn_string

    def __str__(self):
        return f"No connection with {self._neo4j_conn_string}"


class NoDBTableError(APIError):
    def __init__(self, attribute: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._attribute = attribute

    def __str__(self):
        return f"No DB table was found for attribute {self._attribute}"


class NoDBFieldError(APIError):
    def __init__(self, attribute: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._attribute = attribute

    def __str__(self):
        return f"No DB field was found for attribute {self._attribute}"
