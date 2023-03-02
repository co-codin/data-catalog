import logging
from typing import Dict

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.schemas.nodes import SatIn, SatUpdateIn
from app.errors import NodeAlreadyExists, NoNodeError
from app.crud.common import edit_node_fields

logger = logging.getLogger(__name__)


async def add_sat(sat: SatIn, session: AsyncSession) -> int:
    try:
        sat_id = await session.execute_write(_add_sat_tx, sat)
    except ConstraintError:
        raise NodeAlreadyExists('Sat', sat.name)
    else:
        return sat_id


async def edit_sat(sat_name: str, sat: SatUpdateIn, session: AsyncSession) -> int:
    try:
        sat_id = await session.execute_write(_edit_sat_tx, sat_name, sat)
    except ConstraintError:
        raise NodeAlreadyExists('Sat', sat.name)
    else:
        return sat_id


async def remove_sat(sat_name: str, session: AsyncSession):
    sat_id = await session.execute_write(_remove_sat_tx, sat_name)
    return sat_id


async def _add_sat_tx(tx: AsyncManagedTransaction, sat: SatIn):
    create_sat_query = "MATCH (e:Entity {name: $ref_table_name}) " \
                       "CREATE (sat:Sat {name: $name, desc: $desc, db: $db})<-[:SAT {on: [$ref_table_pk, $fk]}]-(e) " \
                       "WITH $attrs as attrs_batch, e, sat " \
                       "UNWIND attrs_batch as attr " \
                       "CREATE (sat)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                       "RETURN ID(e) as hub_id, ID(sat) as sat_id;"
    res = await tx.run(create_sat_query, parameters=sat.dict())
    ids = await res.single()
    if not ids:
        raise NoNodeError('Entity', sat.ref_table_name)
    return ids['sat_id']


async def _edit_sat_tx(tx: AsyncManagedTransaction, sat_name: str, sat: SatUpdateIn):
    sat_id = await _edit_sat_info(tx, sat_name, sat.dict(exclude={'attrs'}))
    await edit_node_fields(tx, sat_id, sat.attrs)
    return sat_id


async def _remove_sat_tx(tx: AsyncManagedTransaction, sat_name: str):
    delete_sat_query = "MATCH (sat:Sat {name: $name}) " \
                       "OPTIONAL MATCH (sat)-[:ATTR]->(f:Field) " \
                       "OPTIONAL MATCH (sat)<-[:SAT]-(:Entity) " \
                       "DETACH DELETE sat, f " \
                       "RETURN ID(sat) as id;"

    res = await tx.run(delete_sat_query, name=sat_name)
    sat_id = await res.single()
    if not sat_id:
        raise NoNodeError('Sat', sat_name)
    return sat_id['id']


async def _edit_sat_info(tx: AsyncManagedTransaction, sat_name: str, sat_info: Dict):
    edit_sat_info_query = "MATCH (sat:Sat {name: $sat_name})<-[r:SAT]-(:Entity {name: $ref_table_name}) " \
                          "SET sat.name=$name, sat.desc=$desc, sat.db=$db, r.on=[$ref_table_pk, $fk] " \
                          "RETURN ID(sat) as id;"

    res = await tx.run(edit_sat_info_query, parameters={'sat_name': sat_name, **sat_info})
    sat_id = await res.single()
    if not sat_id:
        raise NoNodeError('Sat', sat_name)
    return sat_id[0]
