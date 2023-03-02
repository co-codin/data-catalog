import logging

from neo4j import AsyncSession, AsyncManagedTransaction
from typing import Tuple

from app.errors import EntitiesAlreadyLinkedError, NoNodesError, AllNodesExistError
from app.schemas.nodes import LinkIn, OneWayLink

logger = logging.getLogger(__name__)


async def add_link(link: LinkIn, session: AsyncSession) -> Tuple[int, int]:
    link_ids = await session.execute_write(_add_link_tx, link)
    return link_ids


async def _add_link_tx(tx: AsyncManagedTransaction, link: LinkIn) -> Tuple[int, int]:
    one_way_link1, one_way_link2 = link.one_way_links[0], link.one_way_links[1]

    if not await _nodes_exist(tx, 'Entity', one_way_link1.entity_uuid, one_way_link2.entity_uuid):
        raise NoNodesError('Entity', one_way_link1.entity_uuid, one_way_link2.entity_uuid)

    if await _nodes_exist(tx, 'Link', one_way_link1.uuid, one_way_link2.uuid):
        raise AllNodesExistError('Link', one_way_link1.uuid, one_way_link2.uuid)

    await _check_on_hubs_links(tx, one_way_link1, one_way_link2)

    create_link_query = "MATCH (hub1:Entity {uuid: $one_way_link1.entity_uuid }) " \
                        "MATCH (hub2:Entity {uuid: $one_way_link2.entity_uuid }) " \
                        "CREATE (hub1)-[:LINK {on: [$one_way_link1.entity_pk, $one_way_link1.fk]}]->(link1:Link {uuid: coalesce($one_way_link1.uuid, randomUUID()), name: $one_way_link1.name, desc: $one_way_link1.desc, db: $db})-[:LINK {on: [$one_way_link2.fk, $one_way_link2.entity_pk]}]->(hub2) " \
                        "CREATE (hub2)-[:LINK {on: [$one_way_link2.entity_pk, $one_way_link2.fk]}]->(link2:Link {uuid: coalesce($one_way_link2.uuid, randomUUID()), name: $one_way_link2.name, desc: $one_way_link2.desc, db: $db})-[:LINK {on: [$one_way_link1.fk, $one_way_link1.entity_pk]}]->(hub1) " \
                        "WITH $attrs as attrs_batch, link1, link2 " \
                        "UNWIND attrs_batch as attr " \
                        "CREATE (link1)-[:ATTR]->(:Field {name: attr.name, desc: attr.desc, db: attr.db, attrs: attr.attrs, dbtype: attr.dbtype}) " \
                        "RETURN link1.uuid as uuid1, link2.uuid as uuid2;"
    res = await tx.run(
        create_link_query,
        parameters={
            'one_way_link1': one_way_link1.dict(), 'one_way_link2': one_way_link2.dict(),
            **link.dict(include={'attrs', 'db'})
        }
    )
    record = await res.single()
    return record['uuid1'], record['uuid2']


async def _check_on_hubs_links(tx: AsyncManagedTransaction, one_way_link1: OneWayLink, one_way_link2: OneWayLink):
    check_on_hubs_query = "MATCH (hub1:Entity {uuid: $one_way_link1.entity_uuid }) " \
                          "MATCH (hub2:Entity {uuid: $one_way_link2.entity_uuid }) " \
                          "MATCH (hub1)-[:LINK]->(link1:Link)-[:LINK]->(hub2)-[:LINK]->(link2:Link)-[:LINK]->(hub1) " \
                          "RETURN link1.uuid as uuid1, link2.uuid as uuid2;"
    check_on_hubs_query_res = await tx.run(
        check_on_hubs_query,
        parameters={
            'one_way_link1': one_way_link1.dict(), 'one_way_link2': one_way_link2.dict()
        }
    )
    record = await check_on_hubs_query_res.single()
    if record:
        raise EntitiesAlreadyLinkedError((one_way_link1.entity_uuid, one_way_link2.entity_uuid))


async def _nodes_exist(tx: AsyncManagedTransaction, type_: str, *nodes_uuids: str) -> bool:
    cql_query = "UNWIND $nodes_uuids as node_uuid " \
                "MATCH (node {uuid: node_uuid}) " \
                "WHERE $type_ in labels(node) " \
                "RETURN count(node) as count;"
    res = await tx.run(cql_query, type_=type_, nodes_uuids=list(nodes_uuids))
    nodes_len = await res.single()

    logger.info(f"nodes_len is {nodes_len}")

    return len(nodes_uuids) == nodes_len['count']
