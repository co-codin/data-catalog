import logging

from neo4j import AsyncSession, AsyncManagedTransaction
from typing import List, Dict

from app.errors import EntityAlreadyExists, NoEntityError
from app.schemas.nodes import EntityIn, EntityUpdateIn
from app.crud.common import get_cud_fields, entity_exists

logger = logging.getLogger(__name__)


async def add_entity(entity: EntityIn, session: AsyncSession):
    entity_id = await session.execute_write(_add_entity_tx, entity)
    return entity_id


async def edit_entity(hub_name: str, entity: EntityUpdateIn, session: AsyncSession):
    entity_id = await session.execute_write(_edit_entity_tx, hub_name, entity)
    return entity_id


async def remove_entity(hub_name: str, session: AsyncSession):
    entity_id = await session.execute_write(_remove_entity_tx, hub_name)
    return entity_id


async def _add_entity_tx(tx: AsyncManagedTransaction, entity: EntityIn):
    if await entity_exists(tx, entity.name):
        raise EntityAlreadyExists(entity.name)

    create_hub_query = "CREATE (hub:Entity {name: $name, desc: $desc, db: $db}) " \
                       "WITH $attrs as attrs_batch, hub " \
                       "UNWIND attrs_batch as attr " \
                       "CREATE (hub)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                       "RETURN ID(hub) as id;"
    res = await tx.run(create_hub_query, parameters=entity.dict())
    entity_id = await res.single()
    return entity_id['id']


async def _edit_entity_tx(tx: AsyncManagedTransaction, hub_name: str, entity: EntityUpdateIn):
    if not await entity_exists(tx, hub_name):
        raise NoEntityError(hub_name)

    field_ids_res = await _get_hub_field_ids(tx, hub_name)

    # get fields which need to be created, updated and deleted
    fields = await get_cud_fields(entity.attrs, field_ids_res)

    logger.info(f"fields to add {fields.to_create}")
    logger.info(f"fields to update {fields.to_update}")
    logger.info(f"fields to delete {fields.to_delete}")

    await _delete_hub_fields(tx, hub_name, fields.to_delete)
    await _add_hub_fields(tx, hub_name, fields.to_create)
    await _edit_hub_fields(tx, hub_name, fields.to_update)
    entity_id = await _edit_hub_info(tx, hub_name, entity.dict(exclude={'attrs'}))
    return entity_id


async def _remove_entity_tx(tx: AsyncManagedTransaction, hub_name: str):
    if not await entity_exists(tx, hub_name):
        raise NoEntityError(hub_name)

    delete_hub_sat_fields_query = "MATCH (e:Entity {name: $name}) " \
                                  "OPTIONAL MATCH (e)-[:SAT]->(s:Sat) " \
                                  "OPTIONAL MATCH (s)-[r:ATTR]->(f:Field) " \
                                  "DELETE f, r;"

    delete_hub_sat_query = "MATCH (e:Entity {name: $name}) " \
                           "OPTIONAL MATCH (e)-[r:SAT]->(s:Sat) " \
                           "DELETE s, r;"

    delete_hub_query = "MATCH (e:Entity {name: $name}) " \
                       "OPTIONAL MATCH (e)-[r:ATTR]->(f:Field) " \
                       "DELETE f, r, e " \
                       "RETURN ID(e) as id;"

    await tx.run(delete_hub_sat_fields_query, name=hub_name)
    await tx.run(delete_hub_sat_query, name=hub_name)
    res = await tx.run(delete_hub_query, name=hub_name)

    entity_id = await res.single()
    return entity_id['id']


async def _get_hub_field_ids(tx: AsyncManagedTransaction, hub_name: str):
    get_hub_field_ids_query = "MATCH (hub:Entity {name: $hub_name})-[:ATTR]->(f:Field) " \
                              "RETURN ID(f);"

    field_ids_res = await tx.run(get_hub_field_ids_query, hub_name=hub_name)
    return field_ids_res


async def _delete_hub_fields(tx: AsyncManagedTransaction, hub_name: str, fields_to_delete: List[Dict[int, Dict]]):
    if fields_to_delete:
        delete_fields_hub_query = "WITH $attrs as attrs_batch " \
                                  "UNWIND attrs_batch as attr_id " \
                                  "MATCH (hub:Entity {name: $hub_name})-[r:ATTR]->(f:Field) " \
                                  "WHERE ID(f)=attr_id " \
                                  "DELETE r, f;"

        await tx.run(delete_fields_hub_query, hub_name=hub_name, attrs=fields_to_delete)


async def _add_hub_fields(tx: AsyncManagedTransaction, hub_name: str, fields_to_create: List[Dict[int, Dict]]):
    if fields_to_create:
        add_fields_hub_query = "MATCH (hub:Entity {name: $hub_name}) " \
                               "WITH $attrs as attrs_batch, hub " \
                               "UNWIND attrs_batch as attr " \
                               "CREATE (hub)-[:ATTR]->(f:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype});"
        await tx.run(add_fields_hub_query, hub_name=hub_name, attrs=fields_to_create)


async def _edit_hub_fields(tx: AsyncManagedTransaction, hub_name: str, fields_to_update: List[Dict[int, Dict]]):
    edit_fields_hub_query = "MATCH (hub:Entity {name: $hub_name}) " \
                            "WITH $attrs as attrs_batch, hub " \
                            "UNWIND attrs_batch as attr " \
                            "MATCH (hub)-[:ATTR]->(f:Field) " \
                            "WHERE ID(f)=attr.id " \
                            "SET f.name=attr.name, f.desc=attr.desc, f.db=attr.db, f.attrs=attr.attrs, f.dbtype=attr.dbtype;"
    await tx.run(edit_fields_hub_query, hub_name=hub_name, attrs=fields_to_update)


async def _edit_hub_info(tx: AsyncManagedTransaction, hub_name: str, hub_info: Dict):
    logger.info(f"hub_info: {hub_info}")
    edit_hub_info_query = "MATCH (hub:Entity {name: $hub_name}) " \
                          "SET hub.name=$name, hub.desc=$desc, hub.db=$db " \
                          "RETURN ID(hub) as id;"
    res = await tx.run(edit_hub_info_query, parameters={'hub_name': hub_name, **hub_info})
    entity_id = await res.single()
    return entity_id[0]
