import logging
from typing import Tuple

from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError

from app.errors.errors import EntitiesAlreadyLinkedError, NoNodesUUIDError, NoNodeUUIDError, NodeUUIDAlreadyExists
from app.schemas.link import LinkIn, LinkUpdateIn
from app.crud.common import edit_node_fields
from app.cql_queries.link_queries import *

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

    res = await tx.run(create_link_query, link.dict())
    record = await res.single()
    return record['uuid']


async def _edit_link_tx(tx: AsyncManagedTransaction, link_uuid: str, link: LinkUpdateIn):
    await _edit_link_info(tx, link_uuid, link)
    await edit_node_fields(tx, link_uuid, link.fields)


async def _remove_link_tx(tx: AsyncManagedTransaction, link_uuid: str):
    res = await tx.run(delete_link_query, link_uuid=link_uuid)
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(link_uuid)


async def _check_on_hubs_links(tx: AsyncManagedTransaction, ref_tables_uuids: Tuple[str, str]):
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
    res = await tx.run(edit_link_info_query, parameters={'link_uuid': link_uuid, **link.dict()})
    record = await res.single()
    if not record:
        raise NoNodeUUIDError(link_uuid)

    if link.main_link.ref_table_uuid and link.paired_link.ref_table_uuid:
        links_params = {
            'link_uuid': link_uuid,
            **link.dict(
                include={
                    'main_link': {'ref_table_pk', 'fk', 'ref_table_uuid'},
                    'paired_link': {'ref_table_pk', 'fk', 'ref_table_uuid'}
                }
            )
        }
        res = await tx.run(edit_both_hubs_query, parameters=links_params)
        record = await res.single()
        if not record:
            raise NoNodesUUIDError(link.main_link.ref_table_uuid, link.paired_link.ref_table_uuid)
    elif link.main_link.ref_table_uuid:
        link_params = {
            'link_uuid': link_uuid,
            **link.dict(include={'main_link': {'ref_table_pk', 'fk', 'ref_table_uuid'}})
        }
        res = await tx.run(edit_main_hub_query, parameters=link_params)
        record = await res.single()
        if not record:
            raise NoNodeUUIDError(link.main_link.ref_table_uuid)
    elif link.paired_link.ref_table_uuid:
        link_params = {
            'link_uuid': link_uuid,
            **link.dict(include={'paired_link': {'ref_table_pk', 'fk', 'ref_table_uuid'}})
        }
        res = await tx.run(edit_paired_hub_query, parameters=link_params)
        record = await res.single()
        if not record:
            raise NoNodeUUIDError(link.paired_link.ref_table_uuid)


async def _check_on_nodes_existence(tx: AsyncManagedTransaction, type_: str, *nodes_uuids: str):
    res = await tx.run(check_on_nodes_existence_query, type_=type_, nodes_uuids=list(nodes_uuids))
    record = await res.single()
    logger.info(f"count = {record['count']}")
    if record['count'] != len(nodes_uuids):
        raise NoNodesUUIDError(*nodes_uuids)
