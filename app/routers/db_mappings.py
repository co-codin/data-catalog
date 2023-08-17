import typing

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from age import Age

from app.dependencies import ag_session
from app.services.graph import get_attr_db_info

router = APIRouter(
    prefix='/mappings',
    tags=['mappings']
)


class MappingsRequest(BaseModel):
    attributes: typing.List[str]


@router.get('/{attribute}')
async def get_attr_mapping(attribute: str, session: Age = Depends(ag_session)):
    return await get_attr_db_info(session, attribute)


@router.get('/')
async def get_mappings(mappings: MappingsRequest, session: Age = Depends(ag_session)):
    return [
        await get_attr_db_info(session, attribute)
        for attribute in mappings.attributes
    ]
