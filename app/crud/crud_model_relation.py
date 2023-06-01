import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.model import ModelRelation
from app.schemas.model_relation import ModelRelationIn, ModelRelationUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_relations_by_group_id(group_id: str, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .filter(ModelRelation.relation_group_id == group_id)
    )
    model_relation = model_relation.scalars().all()
    return model_relation


async def read_relation_by_guid(guid: str, token: str, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .filter(ModelRelation.guid == guid)
    )

    model_relation = model_relation.scalars().first()

    if not model_relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_relation


async def create_model_relation(relation_in: ModelRelationIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())

    model_relation = ModelRelation(
        **relation_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_relation, relation_in.tags, session)

    session.add(model_relation)
    await session.commit()

    return model_relation.guid


async def update_model_relation(guid: int, relation_update_in: ModelRelationUpdateIn, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .filter(ModelRelation.guid == guid)
    )
    model_relation = model_relation.scalars().first()

    model_relation_update_in_data = {
        key: value for key, value in relation_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelRelation)
        .where(ModelRelation.guid == guid)
        .values(
            **model_relation_update_in_data,
        )
    )

    await update_tags(model_relation, relation_update_in.tags, session)

    session.add(model_relation)
    await session.commit()


async def delete_model_relation(guid: str, session: AsyncSession):
    await session.execute(
        delete(ModelRelation)
        .where(ModelRelation.guid == guid)
    )
    await session.commit()