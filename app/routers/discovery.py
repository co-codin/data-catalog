from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.dependencies import neo4j_session
from app.services.graph import find_entities, describe_entity

router = APIRouter()


@router.get('/search/{search_text}')
async def find(search_text: str, session: AsyncSession = Depends(neo4j_session)):
    return await find_entities(session, search_text)


@router.get('/describe/{entity_name}')
async def describe(entity_name: str, path: str = None, session: AsyncSession = Depends(neo4j_session)):
    return await describe_entity(session, entity_name, path)
