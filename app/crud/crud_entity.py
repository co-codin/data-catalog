import logging

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError
from typing import Dict

from app.errors import NodeAlreadyExists, NoNodeUUIDError
from app.schemas.nodes import EntityIn, EntityUpdateIn
from app.crud.common import edit_node_fields

logger = logging.getLogger(__name__)


async def add_entity(entity: EntityIn, session: AsyncSession) -> str:
    try:
        entity_uuid = await session.execute_write(_add_entity_tx, entity)
    except ConstraintError:
        raise NodeAlreadyExists('Entity', entity.name)
    else:
        return entity_uuid


async def edit_entity(hub_uuid: str, entity: EntityUpdateIn, session: AsyncSession) -> str:
    try:
        entity_uuid = await session.execute_write(_edit_entity_tx, hub_uuid, entity)
    except ConstraintError:
        raise NodeAlreadyExists('Entity', entity.name)
    else:
        return entity_uuid


async def remove_entity(hub_uuid: str, session: AsyncSession) -> str:
    entity_uuid = await session.execute_write(_remove_entity_tx, hub_uuid)
    return entity_uuid


async def _add_entity_tx(tx: AsyncManagedTransaction, entity: EntityIn) -> str:
    create_hub_query = "CREATE (hub:Entity {uuid: coalesce($uuid, randomUUID()), name: $name, desc: $desc, db: $db}) " \
                       "WITH $attrs as attrs_batch, hub " \
                       "UNWIND attrs_batch as attr " \
                       "CREATE (hub)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                       "RETURN hub.uuid as uuid;"
    res = await tx.run(create_hub_query, parameters=entity.dict())
    record = await res.single()
    return record['uuid']


async def _edit_entity_tx(tx: AsyncManagedTransaction, hub_uuid: str, entity: EntityIn) -> str:
    entity_id = await _edit_hub_info(tx, hub_uuid, entity.dict(exclude={'attrs', 'uuid'}))
    await edit_node_fields(tx, hub_uuid, entity.attrs)
    return entity_id


async def _remove_entity_tx(tx: AsyncManagedTransaction, hub_uuid: str) -> str:
    delete_hub_query = "MATCH (e:Entity {uuid: $hub_uuid}) " \
                       "OPTIONAL MATCH (e)-[:SAT]->(s:Sat)-[:ATTR]->(sf:Field) " \
                       "OPTIONAL MATCH (e)-[:ATTR]->(ef:Field) " \
                       "WITH e.uuid as uuid, sf, s, ef, e " \
                       "DETACH DELETE sf, s, ef, e " \
                       "RETURN uuid;"

    res = await tx.run(delete_hub_query, hub_uuid=hub_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError('Entity', hub_uuid)
    return record['uuid']


async def _edit_hub_info(tx: AsyncManagedTransaction, hub_uuid: str, hub_info: Dict[str, Dict]) -> str:
    logger.info(f"hub_info: {hub_info}")
    edit_hub_info_query = "MATCH (hub:Entity {uuid: $hub_uuid}) " \
                          "SET hub.name=$name, hub.desc=$desc, hub.db=$db " \
                          "RETURN hub.uuid as uuid;"
    res = await tx.run(edit_hub_info_query, parameters={'hub_uuid': hub_uuid, **hub_info})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError('Entity', hub_uuid)
    return record['uuid']
