import typing

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from neo4j import Session

from app.dependencies import neo4j_session
from app.services.graph import get_attr_db_info

router = APIRouter()


class MappingsRequest(BaseModel):
    attributes: typing.List[str]


@router.get('/{attribute}')
def get_attr_mapping(attribute: str, session:Session = Depends(neo4j_session)):
    result = get_attr_db_info(session, attribute)
    return result


@router.get('/')
def get_mappings(mappings: MappingsRequest, session:Session = Depends(neo4j_session)):
    result = []
    for attribute in mappings.attributes:
        item = get_attr_db_info(session, attribute)
        result.append(item)

    return result
