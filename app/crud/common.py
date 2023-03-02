import logging
from dataclasses import dataclass, field
from neo4j import AsyncResult, AsyncManagedTransaction
from typing import List, Dict

from app.schemas.nodes import AttributeUpdate

logger = logging.getLogger(__name__)


@dataclass  # CUD - create, update, delete
class CUDFields:
    to_create: List = field(default_factory=list)
    to_update: List = field(default_factory=list)
    to_delete: List = field(default_factory=list)


async def edit_node_fields(tx: AsyncManagedTransaction, node_id: int, attrs):
    field_ids_res = await _get_node_field_ids(tx, node_id)

    # get fields which need to be created, updated and deleted
    fields = await _get_cud_fields(attrs, field_ids_res)

    logger.info(f"fields to add {fields.to_create}")
    logger.info(f"fields to update {fields.to_update}")
    logger.info(f"fields to delete {fields.to_delete}")

    await _delete_node_fields(tx, node_id, fields.to_delete)
    await _add_node_fields(tx, node_id, fields.to_create)
    await _edit_node_fields(tx, node_id, fields.to_update)


async def _get_node_field_ids(tx: AsyncManagedTransaction, node_id: int) -> AsyncResult:
    get_hub_field_ids_query = "MATCH (node)-[:ATTR]->(f:Field) " \
                              "WHERE ID(node)=$id " \
                              "RETURN ID(f);"

    field_ids_res = await tx.run(get_hub_field_ids_query, id=node_id)
    return field_ids_res


async def _get_cud_fields(attrs: List[AttributeUpdate], get_hub_fields_query_res: AsyncResult) -> CUDFields:
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


async def _delete_node_fields(tx: AsyncManagedTransaction, node_id: int, fields_to_delete: List[Dict[int, Dict]]):
    if fields_to_delete:
        delete_fields_hub_query = "WITH $attrs as attrs_batch " \
                                  "UNWIND attrs_batch as attr_id " \
                                  "MATCH (node)-[:ATTR]->(f:Field) " \
                                  "WHERE ID(node)=$id and ID(f)=attr_id " \
                                  "DETACH DELETE f;"

        await tx.run(delete_fields_hub_query, id=node_id, attrs=fields_to_delete)


async def _add_node_fields(tx: AsyncManagedTransaction, node_id: int, fields_to_create: List[Dict[int, Dict]]):
    if fields_to_create:
        add_fields_hub_query = "MATCH (node) " \
                               "WHERE ID(node)=$id " \
                               "WITH $attrs as attrs_batch, node " \
                               "UNWIND attrs_batch as attr " \
                               "CREATE (node)-[:ATTR]->(f:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype});"
        await tx.run(add_fields_hub_query, id=node_id, attrs=fields_to_create)


async def _edit_node_fields(tx: AsyncManagedTransaction, node_id: int, fields_to_update: List[Dict[int, Dict]]):
    if fields_to_update:
        edit_fields_hub_query = "MATCH (node) " \
                                "WHERE ID(node)=$id " \
                                "WITH $attrs as attrs_batch, node " \
                                "UNWIND attrs_batch as attr " \
                                "MATCH (node)-[:ATTR]->(f:Field) " \
                                "WHERE ID(f)=attr.id " \
                                "SET f.name=attr.name, f.desc=attr.desc, f.db=attr.db, f.attrs=attr.attrs, f.dbtype=attr.dbtype;"
        await tx.run(edit_fields_hub_query, id=node_id, attrs=fields_to_update)
