import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.crud_model_version import generate_version_number, VersionLevel
from app.errors.errors import ModelVersionNotDraftError
from app.models.models import ModelRelation, ModelRelationGroup, ModelVersion
from app.schemas.model_relation import ModelRelationIn, ModelRelationUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_relations_by_group_id(group_id: int, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .filter(ModelRelation.model_relation_group_id == group_id)
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


async def check_model_version_is_draft(model_relation_group_id: int, session: AsyncSession):
    model_relation_group = await session.execute(
        select(ModelRelationGroup)
        .filter(ModelRelationGroup.id == model_relation_group_id)
    )
    model_relation_group = model_relation_group.scalars().first()

    model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.id == model_relation_group.model_version_id)
    )
    model_version = model_version.scalars().first()

    if model_version.status != 'draft':
        raise ModelVersionNotDraftError


async def create_model_relation(relation_in: ModelRelationIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())


    await check_model_version_is_draft(model_relation_group_id=relation_in.model_relation_group_id,
                                       session=session)

    model_relation = ModelRelation(
        **relation_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_relation, relation_in.tags, session)

    session.add(model_relation)
    await session.commit()

    model_relation_group = await session.execute(
        select(ModelRelationGroup)
        .filter(ModelRelationGroup.id == model_relation.model_relation_group_id)
    )

    model_relation_group = model_relation_group.scalars().first()
    await generate_version_number(id=model_relation_group.model_version_id, session=session, level=VersionLevel.PATCH)

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

    await update_tags(model_relation, session, relation_update_in.tags)

    session.add(model_relation)
    await session.commit()


async def delete_model_relation(guid: str, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .filter(ModelRelation.guid == guid)
    )
    model_relation = model_relation.scalars().first()

    model_relation_group = await session.execute(
        select(ModelRelationGroup)
        .filter(ModelRelationGroup.id == model_relation.model_relation_group_id)
    )
    model_relation_group = model_relation_group.scalars().first()
    await generate_version_number(id=model_relation_group.model_version_id, session=session, level=VersionLevel.PATCH)

    await session.execute(
        delete(ModelRelation)
        .where(ModelRelation.guid == guid)
    )
    await session.commit()
