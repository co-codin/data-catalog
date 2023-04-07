import typing

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from neo4j import AsyncSession

from app.dependencies import neo4j_session
from app.services.graph import get_attr_db_info

router = APIRouter(
    tags=["mappings"]
)


class MappingsRequest(BaseModel):
    attributes: typing.List[str]


@router.get('/{attribute}')
async def get_attr_mapping(attribute: str, session:AsyncSession = Depends(neo4j_session)):
    return await get_attr_db_info(session, attribute)


@router.get('/')
async def get_mappings(mappings: MappingsRequest, session:AsyncSession = Depends(neo4j_session)):
    return [
        await get_attr_db_info(session, attribute)
        for attribute in mappings.attributes
    ]
