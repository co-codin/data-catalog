import logging
from typing import Tuple

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.errors import EntitiesAlreadyLinkedError, NoNodesUUIDError, NoNodeUUIDError, NodeUUIDAlreadyExists
from app.schemas.link import LinkIn, LinkUpdateIn
from app.crud.common import edit_node_fields

logger = logging.getLogger(__name__)


async def add_link(link: LinkIn, session: AsyncSession) -> str:
    try:
        link_uuid = await session.execute_write(_add_link_tx, link)
    except ConstraintError:
        raise NodeUUIDAlreadyExists(link.uuid)
    else:
        return link_uuid


async def edit_link(link_uuid: str, link: LinkUpdateIn, session: AsyncSession):
    await session.execute_write(_edit_link_tx, link_uuid, link)


async def remove_link(link_uuid: str, session: AsyncSession):
    await session.execute_write(_remove_link_tx, link_uuid)


async def _add_link_tx(tx: AsyncManagedTransaction, link: LinkIn) -> str:
    main_link, paired_link = link.main_link, link.paired_link

    await _check_on_nodes_existence(tx, 'Entity', main_link.ref_table_uuid, paired_link.ref_table_uuid)
    await _check_on_hubs_links(tx, (main_link.ref_table_uuid, paired_link.ref_table_uuid))

    create_link_query = "MATCH (hub1:Entity {uuid: $main_link.ref_table_uuid }) " \
                        "MATCH (hub2:Entity {uuid: $paired_link.ref_table_uuid }) " \
                        "CREATE (hub1)-[:LINK {on: [$main_link.ref_table_pk, $main_link.fk]}]->(link1:Link {uuid: coalesce($uuid, randomUUID()), name: $main_link.name, desc: $main_link.desc, db: $db})-[:LINK {on: [$paired_link.fk, $paired_link.ref_table_pk]}]->(hub2) " \
                        "CREATE (hub2)-[:LINK {on: [$paired_link.ref_table_pk, $paired_link.fk]}]->(link2:Link {name: $paired_link.name, desc: $paired_link.desc, db: $db})-[:LINK {on: [$main_link.fk, $main_link.ref_table_pk]}]->(hub1) " \
                        "WITH $fields as fields_batch, link1, link2 " \
                        "UNWIND fields_batch as field " \
                        "CREATE (link1)-[:ATTR]->(:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype}) " \
                        "RETURN link1.uuid as uuid;"
    res = await tx.run(create_link_query, link.dict())
    record = await res.single()
    return record['uuid']


async def _edit_link_tx(tx: AsyncManagedTransaction, link_uuid: str, link: LinkUpdateIn):
    await _edit_link_info(tx, link_uuid, link)
    await edit_node_fields(tx, link_uuid, link.fields)


async def _remove_link_tx(tx: AsyncManagedTransaction, link_uuid: str):
    delete_sat_query = "MATCH (main_link:Link {uuid: $link_uuid}) " \
                       "MATCH (e1:Entity)-[:LINK]->(main_link)-[:LINK]->(e2:Entity)-[:LINK]->(paired_link:Link)-[:LINK]->(e1:Entity) " \
                       "OPTIONAL MATCH (main_link)-[:SAT]->(mls:Sat)-[:ATTR]->(mlsf:Field) " \
                       "OPTIONAL MATCH (paired_link)-[:SAT]->(pls:Sat)-[:ATTR]->(plsf:Field) " \
                       "OPTIONAL MATCH (main_link)-[:ATTR]->(mlf:Field) " \
                       "OPTIONAL MATCH (paired_link)-[:ATTR]->(plf:Field) " \
                       "WITH main_link.uuid as main_link_uuid, paired_link.uuid as paired_link_uuid, mls, mlsf, pls, plsf, mlf, plf, main_link, paired_link " \
                       "DETACH DELETE mls, mlsf, pls, plsf, mlf, plf, main_link, paired_link " \
                       "RETURN main_link_uuid, paired_link_uuid;"

    res = await tx.run(delete_sat_query, link_uuid=link_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(link_uuid)


async def _check_on_hubs_links(tx: AsyncManagedTransaction, ref_tables_uuids: Tuple[str, str]):
    check_on_hubs_query = "MATCH (hub1:Entity {uuid: $ref_table_uuid1 }) " \
                          "MATCH (hub2:Entity {uuid: $ref_table_uuid2 }) " \
                          "MATCH (hub1)-[:LINK]->(link1:Link)-[:LINK]->(hub2)-[:LINK]->(link2:Link)-[:LINK]->(hub1) " \
                          "RETURN hub1.name as hub1_name, hub2.name as hub2_name;"
    check_on_hubs_query_res = await tx.run(
        check_on_hubs_query,
        parameters={
            'ref_table_uuid1': ref_tables_uuids[0],
            'ref_table_uuid2': ref_tables_uuids[1]
        }
    )
    record = await check_on_hubs_query_res.single()
    if record:
        raise EntitiesAlreadyLinkedError((record['hub1_name'], record['hub2_name']))


async def _edit_link_info(tx: AsyncManagedTransaction, link_uuid: str, link: LinkUpdateIn):
    cql_query = "MATCH (hub1:Entity)-[hub1_main_rel:LINK]->(main_link: Link {uuid: $link_uuid})-[hub2_main_rel:LINK]->(hub2:Entity)-[hub2_paired_rel:LINK]-(paired_link:Link)-[hub1_paired_rel:LINK]->(hub1:Entity) " \
                "SET main_link.desc=$main_link.desc, main_link.name=$main_link.name, main_link.db=$db " \
                "SET paired_link.desc=$paired_link.desc, paired_link.name=$paired_link.name, paired_link.db=$db " \
                "SET hub1_main_rel.on=[$main_link.ref_table_pk, $main_link.fk] " \
                "SET hub2_main_rel.on=[$paired_link.fk, $paired_link.ref_table_pk] " \
                "SET hub2_paired_rel.on=[$paired_link.ref_table_pk, $paired_link.fk] " \
                "SET hub1_paired_rel.on=[$main_link.fk, $main_link.ref_table_pk] " \
                "RETURN main_link.uuid as uuid;"
    res = await tx.run(cql_query, parameters={'link_uuid': link_uuid, **link.dict()})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(link_uuid)


async def _check_on_nodes_existence(tx: AsyncManagedTransaction, type_: str, *nodes_uuids: str):
    cql_query = "UNWIND $nodes_uuids as node_uuid " \
                "MATCH (node {uuid: node_uuid}) " \
                "WHERE $type_ in labels(node) " \
                "RETURN count(node) as count;"
    res = await tx.run(cql_query, type_=type_, nodes_uuids=list(nodes_uuids))
    record = await res.single()
    logger.info(f"count = {record['count']}")
    if record['count'] != len(nodes_uuids):
        raise NoNodesUUIDError('Entity', *nodes_uuids)
