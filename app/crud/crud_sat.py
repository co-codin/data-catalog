import logging
from typing import Dict

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.schemas.sat import SatIn, SatUpdateIn
from app.errors import NoNodeUUIDError, NodeUUIDAlreadyExists
from app.crud.common import edit_node_fields

logger = logging.getLogger(__name__)


async def add_sat(sat: SatIn, session: AsyncSession) -> str:
    try:
        sat_uuid = await session.execute_write(_add_sat_tx, sat)
    except ConstraintError:
        raise NodeUUIDAlreadyExists(sat.uuid)
    else:
        return sat_uuid


async def edit_sat(sat_uuid: str, sat: SatUpdateIn, session: AsyncSession):
    try:
        await session.execute_write(_edit_sat_tx, sat_uuid, sat)
    except ConstraintError:
        raise NodeUUIDAlreadyExists(sat_uuid)


async def remove_sat(sat_uuid: str, session: AsyncSession):
    await session.execute_write(_remove_sat_tx, sat_uuid)


async def _add_sat_tx(tx: AsyncManagedTransaction, sat: SatIn) -> str:
    create_sat_query = "MATCH (node {uuid: $ref_table_uuid}) " \
                       "WHERE node:Entity OR node:Link " \
                       "CREATE (sat:Sat {uuid: coalesce($uuid, randomUUID()), name: $name, desc: $desc, db: $db})<-[:SAT {on: [$ref_table_pk, $fk]}]-(node) " \
                       "WITH $fields as fields_batch, sat " \
                       "UNWIND fields_batch as field " \
                       "CREATE (sat)-[:ATTR]->(:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype}) " \
                       "RETURN sat.uuid as sat_uuid;"
    res = await tx.run(create_sat_query, parameters=sat.dict())
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(sat.ref_table_uuid)
    return record['sat_uuid']


async def _edit_sat_tx(tx: AsyncManagedTransaction, sat_uuid: str, sat: SatUpdateIn):
    await _edit_sat_info(tx, sat_uuid, sat.dict(exclude={'fields'}))
    await edit_node_fields(tx, sat_uuid, sat.fields)


async def _remove_sat_tx(tx: AsyncManagedTransaction, sat_uuid: str):
    delete_sat_query = "MATCH (sat:Sat {uuid: $sat_uuid}) " \
                       "OPTIONAL MATCH (sat)-[:ATTR]->(f:Field) " \
                       "OPTIONAL MATCH (sat)<-[:SAT]-(node) " \
                       "WHERE node:Entity OR node:Link " \
                       "WITH sat.uuid as uuid, sat, f " \
                       "DETACH DELETE sat, f " \
                       "RETURN uuid;"

    res = await tx.run(delete_sat_query, sat_uuid=sat_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(sat_uuid)


async def _edit_sat_info(tx: AsyncManagedTransaction, sat_uuid: str, sat_info: Dict):
    edit_sat_info_query = "MATCH (sat:Sat {uuid: $sat_uuid})<-[r:SAT]-() " \
                          "SET sat.name=$name, sat.desc=$desc, sat.db=$db, r.on=[$ref_table_pk, $fk] " \
                          "RETURN sat.uuid as uuid;"
    res = await tx.run(edit_sat_info_query, parameters={'sat_uuid': sat_uuid, **sat_info})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(sat_uuid)

    if sat_info['ref_table_uuid']:
        edit_sat_info_query = "MATCH (sat:Sat {uuid: $sat_uuid})<-[r:SAT]-() " \
                              "MATCH (node {uuid: $ref_table_uuid}) " \
                              "CREATE (sat)<-[:SAT {on: [$ref_table_pk, $fk]}]-(node) " \
                              "DELETE r " \
                              "RETURN node.uuid as uuid;"

        res = await tx.run(edit_sat_info_query, parameters={'sat_uuid': sat_uuid, **sat_info})
        record = await res.single()
        if not record:
            raise NoNodeUUIDError(sat_info['ref_table_uuid'])
