import logging

from neo4j import AsyncSession, AsyncManagedTransaction, AsyncResult
from typing import List, Dict
from dataclasses import dataclass, field

from app.errors import EntityAlreadyExists, NoEntityError
from app.schemas.nodes import EntityIn, EntityUpdateIn, AttributeUpdate

logger = logging.getLogger(__name__)


# CUD - create, update, delete
@dataclass
class CUDFields:
    to_create: List = field(default_factory=list)
    to_update: List = field(default_factory=list)
    to_delete: List = field(default_factory=list)


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
    if await _entity_exists(tx, entity.name):
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
    if not await _entity_exists(tx, hub_name):
        raise NoEntityError(hub_name)

    field_ids_res = await _get_hub_field_ids(tx, hub_name)

    # get fields which need to be created, updated and deleted
    fields = await _get_cud_fields(entity.attrs, field_ids_res)

    logger.info(f"fields to add {fields.to_create}")
    logger.info(f"fields to update {fields.to_update}")
    logger.info(f"fields to delete {fields.to_delete}")

    await _delete_hub_fields(tx, hub_name, fields.to_delete)
    await _add_hub_fields(tx, hub_name, fields.to_create)
    await _edit_hub_fields(tx, hub_name, fields.to_update)
    entity_id = await _edit_hub_info(tx, hub_name, entity.name, entity.desc, entity.db)
    return entity_id


async def _remove_entity_tx(tx: AsyncManagedTransaction, hub_name: str):
    if not await _entity_exists(tx, hub_name):
        raise NoEntityError(hub_name)

    cql_query = "MATCH (e:Entity {name: $name})-[r:ATTR]->(f:Field) " \
                "DELETE e, r, f " \
                "RETURN ID(e) as id"
    res = await tx.run(cql_query, name=hub_name)
    entity_id = await res.single()
    return entity_id['id']


async def _get_hub_field_ids(tx: AsyncManagedTransaction, hub_name: str):
    get_hub_field_ids_query = "MATCH (hub:Entity {name: $hub_name})-[:ATTR]->(f:Field) " \
                              "RETURN ID(f);"

    field_ids_res = await tx.run(get_hub_field_ids_query, hub_name=hub_name)
    return field_ids_res


async def _get_cud_fields(attrs: List[AttributeUpdate], get_hub_fields_query_res: AsyncResult):
    input_fields = {}
    fields = CUDFields()
    logger.info(f'fields {fields}')

    for field_ in attrs:
        if field_.id is None:
            fields.to_create.append(field_.dict(exclude={'id'}))
        else:
            input_fields[field_.id] = field_.dict()

    async for field_id_res in get_hub_fields_query_res:
        field_id = field_id_res[0]
        try:
            fields.to_update.append(input_fields[field_id])
        except KeyError:
            fields.to_delete.append(field_id)
    return fields


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
                            "SET f.name=attr.name, f.desc=attr.desc, f.db=attr.db, f.attrs=attr.attrs, f.dbtype=attr.dbtype " \
                            "RETURN ID(hub) as id;"
    await tx.run(edit_fields_hub_query, hub_name=hub_name, attrs=fields_to_update)


async def _edit_hub_info(tx: AsyncManagedTransaction, hub_name: str, new_hub_name: str, hub_desc: str, hub_db: str):
    edit_hub_info_query = "MATCH (hub:Entity {name: $hub_name}) " \
                          "SET hub.name=$new_hub_name, hub.desc=$hub_desc, hub.db=$hub_db " \
                          "RETURN ID(hub) as id;"
    res = await tx.run(
        edit_hub_info_query, hub_name=hub_name, new_hub_name=new_hub_name, hub_desc=hub_desc, hub_db=hub_db
    )
    entity_id = await res.single()
    return entity_id[0]


async def _entity_exists(tx: AsyncManagedTransaction, hub_name: str):
    result = await tx.run("MATCH (hub:Entity {name: $name}) RETURN ID(hub) as id;", name=hub_name)
    hub_id = await result.single()
    return hub_id is not None
