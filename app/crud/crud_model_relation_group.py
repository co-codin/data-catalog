import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.model import ModelRelationGroup, ModelRelation
from app.schemas.model_relation_group import ModelRelationGroupIn, ModelRelationGroupUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_relation_groups(session: AsyncSession):
    relation_groups = await session.execute(
        select(ModelRelationGroup)
    )
    model_relation_groups = relation_groups.scalars().all()
    return model_relation_groups


async def read_relation_group_by_guid(guid: str, token: str, session: AsyncSession):
    model_relation_group = await session.execute(
        select(ModelRelationGroup)
        .options(selectinload(ModelRelationGroup.tags))
        .filter(ModelRelationGroup.guid == guid)
    )

    model_relation_group = model_relation_group.scalars().first()

    if not model_relation_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_relation_group


async def create_model_relation_group(relation_group_in: ModelRelationGroupIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())

    model_relation_group = ModelRelationGroup(
        **relation_group_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_relation_group, relation_group_in.tags, session)

    session.add(model_relation_group)
    await session.commit()

    return model_relation_group.guid


async def update_model_relation_group(guid: int, relation_group_update_in: ModelRelationGroupUpdateIn, session: AsyncSession):
    model_relation_group = await session.execute(
        select(ModelRelationGroup)
        .options(selectinload(ModelRelationGroup.tags))
        .filter(ModelRelationGroup.guid == guid)
    )
    model_relation_group = model_relation_group.scalars().first()

    model_relation_group_update_in_data = {
        key: value for key, value in relation_group_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelRelationGroup)
        .where(ModelRelationGroup.guid == guid)
        .values(
            **model_relation_group_update_in_data,
        )
    )

    await update_tags(model_relation_group, session, relation_group_update_in.tags)

    session.add(model_relation_group)
    await session.commit()


async def delete_model_relation_group(guid: str, session: AsyncSession):
    model_relation_group = await session.execute(
        select(ModelRelationGroup)
        .filter(ModelRelationGroup.guid == guid)
    )
    model_relation_group = model_relation_group.scalars().first()

    await session.execute(
        delete(ModelRelation)
        .where(ModelRelation.model_relation_group_id == model_relation_group.id)
    )

    await session.execute(
        delete(ModelRelationGroup)
        .where(ModelRelationGroup.guid == guid)
    )
    await session.commit()