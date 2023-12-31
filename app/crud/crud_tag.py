from typing import Iterable

from sqlalchemy import select, delete, and_
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Operation, ModelQuality, ModelRelation, ModelResource, ModelResourceAttribute, ModelVersion, Pipeline, OperationBody
)
from app.models.queries import Query
from app.models.sources import SourceRegister, Object, Field, Model
from app.models.tags import Tag
from app.database.sqlalchemy import db_session


async def add_tags(
        tags_like_model: (
                SourceRegister | Object | Field | Model | Operation | ModelQuality | OperationBody
                | ModelRelation | ModelResource | ModelResourceAttribute | ModelVersion | Pipeline | Query
        ),
        tags_in: Iterable[str],
        session: AsyncSession
):
    if not tags_in:
        return

    tag_models = await session.execute(
        select(Tag)
        .filter(Tag.name.in_(tags_in))
    )
    tag_models = tag_models.scalars().all()
    tag_models_set = {tag.name for tag in tag_models}

    tags_like_model.tags.extend(tag_models)
    tags_like_model.tags.extend(
        (Tag(name=tag) for tag in tags_in if tag not in tag_models_set)
    )


async def update_tags(
        tags_like_model: (
                SourceRegister | Object | Model | Field | Operation | ModelQuality | OperationBody
                | ModelRelation | ModelResource | ModelResourceAttribute | ModelVersion | Pipeline | Query
        ),
        session: AsyncSession, tags_update_in: list[str] | None
):
    if tags_update_in is not None:
        tags_update_in_set = {tag for tag in tags_update_in}
        tags_model_set = {tag.name for tag in tags_like_model.tags}
        tags_model_dict = {tag.name: tag for tag in tags_like_model.tags}

        tags_to_delete = tags_model_set - tags_update_in_set
        for tag in tags_to_delete:
            tags_like_model.tags.remove(tags_model_dict[tag])

        tags_to_create = tags_update_in_set - tags_model_set
        await add_tags(tags_like_model, tags_to_create, session)


async def remove_redundant_tags():
    async with db_session() as session:
        tags = await session.execute(
            select(Tag)
            .options(
                load_only(Tag.id),
                joinedload(Tag.source_registries),
                joinedload(Tag.objects),
                joinedload(Tag.fields),
                joinedload(Tag.models),
                joinedload(Tag.model_versions),
                joinedload(Tag.model_qualities),
                joinedload(Tag.model_relations),
                joinedload(Tag.model_resources),
                joinedload(Tag.model_resource_attributes),
                joinedload(Tag.operations),
                joinedload(Tag.operation_bodies),
                joinedload(Tag.queries),
                joinedload(Tag.pipelines)
            )
            .where(
                and_(
                    ~Tag.source_registries.any(),
                    ~Tag.objects.any(),
                    ~Tag.fields.any(),
                    ~Tag.models.any(),
                    ~Tag.model_versions.any(),
                    ~Tag.model_qualities.any(),
                    ~Tag.model_relations.any(),
                    ~Tag.model_resources.any(),
                    ~Tag.model_resource_attributes.any(),
                    ~Tag.operations.any(),
                    ~Tag.operation_bodies.any(),
                    ~Tag.queries.any(),
                    ~Tag.pipelines.any()
                )
            )
        )

        tags = tags.scalars().unique()
        if not tags:
            return

        tag_ids = [tag.id for tag in tags]
        await session.execute(
            delete(Tag)
            .where(Tag.id.in_(tag_ids))
        )
        await session.commit()
