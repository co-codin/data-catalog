from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.entity import EntityIn, EntityUpdateIn
from app.dependencies import neo4j_session
from app.crud.crud_entity import add_entity, edit_entity, remove_entity

router = APIRouter(
    prefix='/hubs',
    tags=['hubs']
)

@router.get('')
async def get_entities(session: AsyncSession = Depends(neo4j_session)):
    pass

@router.post('/')
async def create_entity(entity_in: EntityIn, session: AsyncSession = Depends(neo4j_session)):
    entity_uuid = await add_entity(entity_in, session)
    return {'message': f'entity {entity_in.name} was created', 'uuid': entity_uuid}


@router.put('/{hub_uuid}/')
async def update_entity(hub_uuid: str, entity_in: EntityUpdateIn, session: AsyncSession = Depends(neo4j_session)):
    await edit_entity(hub_uuid, entity_in, session)
    return {'message': f'entity was updated'}


@router.delete('/{hub_uuid}/')
async def delete_entity(hub_uuid: str, session: AsyncSession = Depends(neo4j_session)):
    await remove_entity(hub_uuid, session)
    return {'message': f'entity was deleted'}
