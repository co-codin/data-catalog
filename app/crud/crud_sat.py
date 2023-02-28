import logging
from typing import List, Dict

from neo4j import AsyncSession, AsyncManagedTransaction

from app.schemas.nodes import SatIn, SatUpdateIn
from app.errors import SatAlreadyExists, NoEntityError, NoSatError
from app.crud.common import get_cud_fields, entity_exists

logger = logging.getLogger(__name__)


async def add_sat(sat: SatIn, session: AsyncSession):
    sat_id = await session.execute_write(_add_sat_tx, sat)
    return sat_id


async def edit_sat(sat_name: str, sat: SatUpdateIn, session: AsyncSession):
    sat_id = await session.execute_write(_edit_sat_tx, sat_name, sat)
    return sat_id


async def remove_sat(sat_name: str, session: AsyncSession):
    sat_id = await session.execute_write(_remove_sat_tx, sat_name)
    return sat_id


async def _add_sat_tx(tx: AsyncManagedTransaction, sat: SatIn):
    if await _sat_exists(tx, sat.name):
        raise SatAlreadyExists(sat.name)

    if not await entity_exists(tx, sat.ref_table_name):
        raise NoEntityError(sat.ref_table_name)

    create_sat_query = "MATCH (e:Entity {name: $ref_table_name}) " \
                       "CREATE (sat:Sat {name: $name, desc: $desc, db: $db})<-[:SAT {on: [$ref_table_pk, $fk]}]-(e) " \
                       "WITH $attrs as attrs_batch, sat " \
                       "UNWIND attrs_batch as attr " \
                       "CREATE (sat)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                       "RETURN ID(sat) as id;"
    res = await tx.run(create_sat_query, parameters=sat.dict())
    sat_id = await res.single()
    return sat_id['id']


async def _edit_sat_tx(tx: AsyncManagedTransaction, sat_name: str, sat: SatUpdateIn):
    if not await _sat_exists(tx, sat_name):
        raise NoSatError(sat_name)

    field_ids_res = await _get_sat_field_ids(tx, sat_name)

    # get fields which need to be created, updated and deleted
    fields = await get_cud_fields(sat.attrs, field_ids_res)

    logger.info(f"fields to add {fields.to_create}")
    logger.info(f"fields to update {fields.to_update}")
    logger.info(f"fields to delete {fields.to_delete}")

    await _delete_sat_fields(tx, sat_name, fields.to_delete)
    await _add_sat_fields(tx, sat_name, fields.to_create)
    await _edit_sat_fields(tx, sat_name, fields.to_update)
    entity_id = await _edit_sat_info(tx, sat_name, sat.dict(exclude={'attrs'}))
    return entity_id


async def _remove_sat_tx(tx: AsyncManagedTransaction, sat_name: str):
    if not await _sat_exists(tx, sat_name):
        raise NoSatError(sat_name)

    cql_query = "MATCH (sat:Sat {name: $name}) " \
                "OPTIONAL MATCH (sat)-[ra:ATTR]->(f:Field) " \
                "OPTIONAL MATCH (sat)<-[rs:SAT]-(:Entity) " \
                "DELETE sat, ra, f, rs " \
                "RETURN ID(sat) as id;"
    res = await tx.run(cql_query, name=sat_name)
    sat_id = await res.single()
    return sat_id['id']


async def _get_sat_field_ids(tx: AsyncManagedTransaction, sat_name: str):
    get_sat_field_ids_query = "MATCH (sat:Sat {name: $sat_name})-[:ATTR]->(f:Field) " \
                              "RETURN ID(f);"

    field_ids_res = await tx.run(get_sat_field_ids_query, sat_name=sat_name)
    return field_ids_res


async def _delete_sat_fields(tx: AsyncManagedTransaction, sat_name: str, fields_to_delete: List[Dict[int, Dict]]):
    if fields_to_delete:
        delete_fields_sat_query = "WITH $attrs as attrs_batch " \
                                  "UNWIND attrs_batch as attr_id " \
                                  "MATCH (sat:Sat {name: $sat_name})-[r:ATTR]->(f:Field) " \
                                  "WHERE ID(f)=attr_id " \
                                  "DELETE r, f;"

        await tx.run(delete_fields_sat_query, sat_name=sat_name, attrs=fields_to_delete)


async def _add_sat_fields(tx: AsyncManagedTransaction, sat_name: str, fields_to_create: List[Dict[int, Dict]]):
    if fields_to_create:
        add_fields_sat_query = "MATCH (sat:Sat {name: $sat_name}) " \
                               "WITH $attrs as attrs_batch, sat " \
                               "UNWIND attrs_batch as attr " \
                               "CREATE (sat)-[:ATTR]->(f:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype});"
        await tx.run(add_fields_sat_query, sat_name=sat_name, attrs=fields_to_create)


async def _edit_sat_fields(tx: AsyncManagedTransaction, sat_name: str, fields_to_update: List[Dict[int, Dict]]):
    edit_fields_sat_query = "MATCH (sat:Sat {name: $sat_name}) " \
                            "WITH $attrs as attrs_batch, sat " \
                            "UNWIND attrs_batch as attr " \
                            "MATCH (sat)-[:ATTR]->(f:Field) " \
                            "WHERE ID(f)=attr.id " \
                            "SET f.name=attr.name, f.desc=attr.desc, f.db=attr.db, f.attrs=attr.attrs, f.dbtype=attr.dbtype;"
    await tx.run(edit_fields_sat_query, sat_name=sat_name, attrs=fields_to_update)


async def _edit_sat_info(tx: AsyncManagedTransaction, sat_name: str, sat_info: Dict):
    edit_sat_info_query = "MATCH (sat:Sat {name: $sat_name})<-[r:SAT]-(:Entity {name: $ref_table_name}) " \
                          "SET sat.name=$name, sat.desc=$desc, sat.db=$db, r.on=[$ref_table_pk, $fk] " \
                          "RETURN ID(sat) as id;"

    res = await tx.run(edit_sat_info_query, parameters={'sat_name': sat_name, **sat_info})
    sat_id = await res.single()
    return sat_id[0]


async def _sat_exists(tx: AsyncManagedTransaction, sat_name: str):
    result = await tx.run("MATCH (sat:Sat {name: $name}) RETURN ID(sat) as id;", name=sat_name)
    hub_id = await result.single()
    return hub_id is not None
