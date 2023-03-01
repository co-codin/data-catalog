from fastapi import status


class APIError(Exception):
    status_code: int


class NoNodeError(APIError):
    def __init__(self, type_: str, name: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._type = type_
        self._name = name

    def __str__(self):
        return f"{self._type} {self._name} doesn't exist"


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


class CyclicPathError(APIError):
    def __init__(self, path: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._path = path

    def __str__(self):
        return f"Cyclic path was given: {self._path}"


class NodeAlreadyExists(APIError):
    def __init__(self, type_: str, name: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._type = type_
        self._name = name

    def __str__(self):
        return f"{self._type} {self._name} already exists"
