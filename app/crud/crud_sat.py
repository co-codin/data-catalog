import logging
from typing import Dict

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.schemas.nodes import SatIn, SatUpdateIn
from app.errors import NodeAlreadyExists, NoNodeUUIDError
from app.crud.common import edit_node_fields

logger = logging.getLogger(__name__)


async def add_sat(sat: SatIn, session: AsyncSession) -> str:
    try:
        sat_uuid = await session.execute_write(_add_sat_tx, sat)
    except ConstraintError:
        raise NodeAlreadyExists('Sat', sat.name)
    else:
        return sat_uuid


async def edit_sat(sat_uuid: str, sat: SatUpdateIn, session: AsyncSession) -> str:
    try:
        sat_uuid = await session.execute_write(_edit_sat_tx, sat_uuid, sat)
    except ConstraintError:
        raise NodeAlreadyExists('Sat', sat.name)
    else:
        return sat_uuid


async def remove_sat(sat_uuid: str, session: AsyncSession) -> str:
    sat_uuid = await session.execute_write(_remove_sat_tx, sat_uuid)
    return sat_uuid


async def _add_sat_tx(tx: AsyncManagedTransaction, sat: SatIn) -> str:
    create_sat_query = "MATCH (e:Entity {uuid: $ref_table_uuid}) " \
                       "CREATE (sat:Sat {uuid: coalesce($uuid, randomUUID()), name: $name, desc: $desc, db: $db})<-[:SAT {on: [$ref_table_pk, $fk]}]-(e) " \
                       "WITH $attrs as attrs_batch, e, sat " \
                       "UNWIND attrs_batch as attr " \
                       "CREATE (sat)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                       "RETURN sat.uuid as sat_uuid;"
    res = await tx.run(create_sat_query, parameters=sat.dict())
    record = await res.single()
    if not record:
        raise NoNodeUUIDError('Entity', sat.ref_table_uuid)
    return record['sat_uuid']


async def _edit_sat_tx(tx: AsyncManagedTransaction, sat_uuid: str, sat: SatUpdateIn) -> str:
    sat_uuid = await _edit_sat_info(tx, sat_uuid, sat.dict(exclude={'attrs'}))
    await edit_node_fields(tx, sat_uuid, sat.attrs)
    return sat_uuid


async def _remove_sat_tx(tx: AsyncManagedTransaction, sat_uuid: str) -> str:
    delete_sat_query = "MATCH (sat:Sat {uuid: $sat_uuid}) " \
                       "OPTIONAL MATCH (sat)-[:ATTR]->(f:Field) " \
                       "OPTIONAL MATCH (sat)<-[:SAT]-(:Entity) " \
                       "WITH sat.uuid as uuid, sat, f " \
                       "DETACH DELETE sat, f " \
                       "RETURN uuid;"

    res = await tx.run(delete_sat_query, sat_uuid=sat_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError('Sat', sat_uuid)
    return record['uuid']


async def _edit_sat_info(tx: AsyncManagedTransaction, sat_uuid: str, sat_info: Dict) -> str:
    edit_sat_info_query = "MATCH (sat:Sat {uuid: $sat_uuid})<-[r:SAT]-() " \
                          "SET sat.name=$name, sat.desc=$desc, sat.db=$db, r.on=[$ref_table_pk, $fk] " \
                          "RETURN sat.uuid as uuid;"

    res = await tx.run(edit_sat_info_query, parameters={'sat_uuid': sat_uuid, **sat_info})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError('Sat', sat_uuid)
    return record['uuid']
