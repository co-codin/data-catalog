from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import EntityIn
from app.dependencies import neo4j_session

router = APIRouter()


@router.post('/')
async def create_entity(entity_in: EntityIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.put('/{hub_name}/')
async def update_entity(hub_name: str, entity_in: EntityIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.delete('/{hub_name}/')
async def delete_entity(hub_name: str, session: AsyncSession = Depends(neo4j_session)):
    ...

