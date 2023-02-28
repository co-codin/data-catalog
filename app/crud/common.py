import logging
from dataclasses import dataclass, field
from neo4j import AsyncResult, AsyncManagedTransaction
from typing import List

from app.schemas.nodes import AttributeUpdate

logger = logging.getLogger(__name__)


@dataclass  # CUD - create, update, delete
class CUDFields:
    to_create: List = field(default_factory=list)
    to_update: List = field(default_factory=list)
    to_delete: List = field(default_factory=list)


async def get_cud_fields(attrs: List[AttributeUpdate], get_hub_fields_query_res: AsyncResult) -> CUDFields:
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


async def entity_exists(tx: AsyncManagedTransaction, hub_name: str):
    result = await tx.run("MATCH (hub:Entity {name: $name}) RETURN ID(hub) as id;", name=hub_name)
    hub_id = await result.single()
    return hub_id is not None
