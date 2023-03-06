import logging

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError
from typing import Dict

from app.crud.crud_link import _remove_link_tx
from app.errors import NodeNameAlreadyExists, NoNodeUUIDError, NodeUUIDAlreadyExists
from app.schemas.entity import EntityIn, EntityUpdateIn
from app.crud.common import edit_node_fields
from app.cql_queries.entity_queries import *

logger = logging.getLogger(__name__)


async def add_entity(entity: EntityIn, session: AsyncSession) -> str:
    try:
        entity_uuid = await session.execute_write(_add_entity_tx, entity)
    except ConstraintError:
        raise NodeNameAlreadyExists('Entity', entity.name)
    else:
        return entity_uuid


async def edit_entity(hub_uuid: str, entity: EntityUpdateIn, session: AsyncSession):
    try:
        await session.execute_write(_edit_entity_tx, hub_uuid, entity)
    except ConstraintError:
        raise NodeUUIDAlreadyExists(hub_uuid)


async def remove_entity(hub_uuid: str, session: AsyncSession):
    await session.execute_write(_remove_entity_tx, hub_uuid)


async def _add_entity_tx(tx: AsyncManagedTransaction, entity: EntityIn) -> str:
    res = await tx.run(create_hub_query, parameters=entity.dict())
    record = await res.single()
    return record['uuid']


async def _edit_entity_tx(tx: AsyncManagedTransaction, hub_uuid: str, entity: EntityIn):
    await _edit_hub_info(tx, hub_uuid, entity.dict(exclude={'fields', 'uuid'}))
    await edit_node_fields(tx, hub_uuid, entity.fields)


async def _remove_entity_tx(tx: AsyncManagedTransaction, hub_uuid: str):
    link_res = await tx.run(match_link_query, hub_uuid=hub_uuid)
    link_record = await link_res.single()

    if link_record['uuid']:
        await _remove_link_tx(tx, link_record['uuid'])

    res = await tx.run(delete_hub_query, hub_uuid=hub_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(hub_uuid)


async def _edit_hub_info(tx: AsyncManagedTransaction, hub_uuid: str, hub_info: Dict[str, Dict]):
    logger.info(f"hub_info: {hub_info}")
    res = await tx.run(edit_hub_info_query, parameters={'hub_uuid': hub_uuid, **hub_info})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(hub_uuid)
