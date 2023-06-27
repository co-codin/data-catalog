from typing import Tuple

from fastapi import status
from app.errors import APIError


class NoNodeNameError(APIError):
    def __init__(self, type_: str, name: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._type = type_
        self._name = name

    def __str__(self):
        return f"{self._type} {self._name} doesn't exist"


class NoNodeUUIDError(APIError):
    def __init__(self, uuid_: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._uuid = uuid_

    def __str__(self):
        return f"Node with uuid={self._uuid} doesn't exist"


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


class NodeNameAlreadyExists(APIError):
    def __init__(self, type_: str, name: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._type = type_
        self._name = name

    def __str__(self):
        return f"{self._type} {self._name} already exists"


class NodeUUIDAlreadyExists(APIError):
    def __init__(self, uuid_: str):
        self.status_code = status.HTTP_404_NOT_FOUND
        self._uuid = uuid_

    def __str__(self):
        return f"Node with uuid={self._uuid} already exists"


class EntitiesAlreadyLinkedError(APIError):
    def __init__(self, entities: Tuple[str, str]):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._entities = entities

    def __str__(self):
        return f"Entities {self._entities[0]} and {self._entities[1]} are already linked"


class NoNodesUUIDError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        nodes_string = ', '.join(self._nodes)
        return f"Some of the following nodes with uuids: {nodes_string} are missing"


class AttributeDataTypeError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Attribute hasn't any data_type link"


class AttributeDataTypeOverflowError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Attribute can have only one data_type link"


class ModelNameAlreadyExist(APIError):
    def __init__(self, name: str):
        self.status_code = status.HTTP_409_CONFLICT
        self._name = name

    def __str__(self):
        return f'model name {self._name} already exists'


class OperationNameAlreadyExist(ModelNameAlreadyExist):
    def __str__(self):
        return f'operation name {self._name} already exists'


class OperationInputParametersNotExists(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return 'Operation should have one input parameter as minimum'


class OperationOutputParameterNotExists(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return 'Operation should have one output parameter'


class OperationParametersNameAlreadyExist(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "All input parameters names in one operation should be unique"


class ModelAttitudeAttributesError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Resource attributes in one attitude can't be equals and must be valid"


class ModelVersionNotDraftError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Model version isn't in draft status"


class ModelResourceHasAttributesError(APIError):
    def __init__(self, *nodes: str):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self._nodes = nodes

    def __str__(self):
        return "Model resource can't be remove becouse has attributes"
