import logging

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError
from typing import Dict

from app.errors import NodeAlreadyExists, NoNodeError
from app.schemas.nodes import EntityIn, EntityUpdateIn
from app.crud.common import edit_node_fields

logger = logging.getLogger(__name__)


async def add_entity(entity: EntityIn, session: AsyncSession) -> int:
    try:
        entity_id = await session.execute_write(_add_entity_tx, entity)
    except ConstraintError:
        raise NodeAlreadyExists('Entity', entity.name)
    else:
        return entity_id


async def edit_entity(hub_name: str, entity: EntityUpdateIn, session: AsyncSession) -> int:
    try:
        entity_id = await session.execute_write(_edit_entity_tx, hub_name, entity)
    except ConstraintError:
        raise NodeAlreadyExists('Entity', entity.name)
    else:
        return entity_id


async def remove_entity(hub_name: str, session: AsyncSession):
    entity_id = await session.execute_write(_remove_entity_tx, hub_name)
    return entity_id


async def _add_entity_tx(tx: AsyncManagedTransaction, entity: EntityIn):
    create_hub_query = "CREATE (hub:Entity {name: $name, desc: $desc, db: $db}) " \
                       "WITH $attrs as attrs_batch, hub " \
                       "UNWIND attrs_batch as attr " \
                       "CREATE (hub)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                       "RETURN ID(hub) as id;"
    res = await tx.run(create_hub_query, parameters=entity.dict())
    entity_id = await res.single()
    return entity_id['id']


async def _edit_entity_tx(tx: AsyncManagedTransaction, hub_name: str, entity: EntityUpdateIn):
    entity_id = await _edit_hub_info(tx, hub_name, entity.dict(exclude={'attrs'}))
    await edit_node_fields(tx, entity_id, entity.attrs)
    return entity_id


async def _remove_entity_tx(tx: AsyncManagedTransaction, hub_name: str):
    delete_hub_query = "MATCH (e:Entity {name: $name}) " \
                       "OPTIONAL MATCH (e)-[:SAT]->(s:Sat)-[:ATTR]->(sf:Field) " \
                       "OPTIONAL MATCH (e)-[:ATTR]->(ef:Field) " \
                       "DETACH DELETE sf, ef, s, e " \
                       "RETURN ID(e) as id;"

    res = await tx.run(delete_hub_query, name=hub_name)
    entity_id = await res.single()
    if not entity_id:
        raise NoNodeError('Entity', hub_name)
    return entity_id['id']


async def _edit_hub_info(tx: AsyncManagedTransaction, hub_name: str, hub_info: Dict[str, Dict]):
    logger.info(f"hub_info: {hub_info}")
    edit_hub_info_query = "MATCH (hub:Entity {name: $hub_name}) " \
                          "SET hub.name=$name, hub.desc=$desc, hub.db=$db " \
                          "RETURN ID(hub) as id;"
    res = await tx.run(edit_hub_info_query, parameters={'hub_name': hub_name, **hub_info})
    entity_id = await res.single()
    if not entity_id:
        raise NoNodeError('Entity', hub_name)
    return entity_id[0]
