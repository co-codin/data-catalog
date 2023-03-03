import logging
from dataclasses import dataclass, field
from neo4j import AsyncResult, AsyncManagedTransaction
from typing import List, Dict

from app.schemas.nodes import FieldUpdate

logger = logging.getLogger(__name__)


@dataclass  # CUD - create, update, delete
class CUDFields:
    to_create: List = field(default_factory=list)
    to_update: List = field(default_factory=list)
    to_delete: List = field(default_factory=list)


async def edit_node_fields(tx: AsyncManagedTransaction, node_uuid: str, input_fields):
    field_ids_res = await _get_node_field_ids(tx, node_uuid)

    # get fields which need to be created, updated and deleted
    fields = await _get_cud_fields(input_fields, field_ids_res)

    logger.info(f"fields to add {fields.to_create}")
    logger.info(f"fields to update {fields.to_update}")
    logger.info(f"fields to delete {fields.to_delete}")

    await _delete_node_fields(tx, node_uuid, fields.to_delete)
    await _add_node_fields(tx, node_uuid, fields.to_create)
    await _edit_node_fields(tx, node_uuid, fields.to_update)


async def _get_node_field_ids(tx: AsyncManagedTransaction, node_uuid: str) -> AsyncResult:
    get_node_field_ids_query = "MATCH (node {uuid: $node_uuid})-[:ATTR]->(f:Field) " \
                              "RETURN ID(f);"

    res = await tx.run(get_node_field_ids_query, node_uuid=node_uuid)
    return res


async def _get_cud_fields(input_fields: List[FieldUpdate], get_node_fields_query_res: AsyncResult) -> CUDFields:
    input_fields_dict = {}
    fields = CUDFields()
    logger.info(f'fields {fields}')

    for field_ in input_fields:
        if field_.id is None:
            fields.to_create.append(field_.dict(exclude={'id'}))
        else:
            input_fields_dict[field_.id] = field_.dict()

    async for field_id_res in get_node_fields_query_res:
        field_id = field_id_res[0]
        try:
            fields.to_update.append(input_fields_dict[field_id])
        except KeyError:
            fields.to_delete.append(field_id)
    return fields


async def _delete_node_fields(tx: AsyncManagedTransaction, node_uuid: str, fields_to_delete: List[Dict[int, Dict]]):
    if fields_to_delete:
        delete_fields_hub_query = "WITH $fields as fields_batch " \
                                  "UNWIND fields_batch as field_id " \
                                  "MATCH (node {uuid: $node_uuid})-[:ATTR]->(f:Field) " \
                                  "WHERE ID(f)=field_id " \
                                  "DETACH DELETE f;"

        await tx.run(delete_fields_hub_query, node_uuid=node_uuid, fields=fields_to_delete)


async def _add_node_fields(tx: AsyncManagedTransaction, node_uuid: str, fields_to_create: List[Dict[int, Dict]]):
    if fields_to_create:
        add_fields_hub_query = "MATCH (node {uuid: $node_uuid}) " \
                               "WITH $fields as fields_batch, node " \
                               "UNWIND fields_batch as field " \
                               "CREATE (node)-[:ATTR]->(f:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype});"
        await tx.run(add_fields_hub_query, node_uuid=node_uuid, fields=fields_to_create)


async def _edit_node_fields(tx: AsyncManagedTransaction, node_uuid: str, fields_to_update: List[Dict[int, Dict]]):
    if fields_to_update:
        edit_fields_hub_query = "MATCH (node {uuid: $node_uuid}) " \
                                "WITH $fields as fields_batch, node " \
                                "UNWIND fields_batch as field " \
                                "MATCH (node)-[:ATTR]->(f:Field) " \
                                "WHERE ID(f)=field.id " \
                                "SET f.name=field.name, f.desc=field.desc, f.db=field.db, f.attrs=field.attrs, f.dbtype=field.dbtype;"
        await tx.run(edit_fields_hub_query, node_uuid=node_uuid, fields=fields_to_update)

