from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import EntityIn, EntityUpdateIn
from app.dependencies import neo4j_session
from app.crud.crud_entity import add_entity, edit_entity, remove_entity

router = APIRouter()


@router.post('/')
async def create_entity(entity_in: EntityIn, session: AsyncSession = Depends(neo4j_session)):
    entity_id = await add_entity(entity_in, session)
    return {'status': 'ok', 'message': f'entity {entity_in.name} was created', 'id': entity_id}


@router.put('/{hub_name}/')
async def update_entity(hub_name: str, entity_in: EntityUpdateIn, session: AsyncSession = Depends(neo4j_session)):
    entity_id = await edit_entity(hub_name, entity_in, session)
    return {'status': 'ok', 'message': f'entity {hub_name} was updated', 'id': entity_id}


@router.delete('/{hub_name}/')
async def delete_entity(hub_name: str, session: AsyncSession = Depends(neo4j_session)):
    entity_id = await remove_entity(hub_name, session)
    return {'status': 'ok', 'message': f'entity {hub_name} was deleted', 'id': entity_id}
