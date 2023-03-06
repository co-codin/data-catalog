import logging
from typing import Dict

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.schemas.sat import SatIn, SatUpdateIn
from app.errors import NoNodeUUIDError, NodeUUIDAlreadyExists
from app.crud.common import edit_node_fields
from app.cql_queries.sat_queries import *

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
    res = await tx.run(create_sat_query, parameters=sat.dict())
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(sat.ref_table_uuid)
    return record['sat_uuid']


async def _edit_sat_tx(tx: AsyncManagedTransaction, sat_uuid: str, sat: SatUpdateIn):
    await _edit_sat_info(tx, sat_uuid, sat.dict(exclude={'fields'}))
    await edit_node_fields(tx, sat_uuid, sat.fields)


async def _remove_sat_tx(tx: AsyncManagedTransaction, sat_uuid: str):
    res = await tx.run(delete_sat_query, sat_uuid=sat_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(sat_uuid)


async def _edit_sat_info(tx: AsyncManagedTransaction, sat_uuid: str, sat_info: Dict):
    res = await tx.run(edit_sat_info_query, parameters={'sat_uuid': sat_uuid, **sat_info})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(sat_uuid)

    if sat_info['ref_table_uuid']:
        res = await tx.run(edit_sat_link_query, parameters={'sat_uuid': sat_uuid, **sat_info})
        record = await res.single()
        if not record:
            raise NoNodeUUIDError(sat_info['ref_table_uuid'])
