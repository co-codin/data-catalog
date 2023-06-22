from typing import Iterable

from sqlalchemy import select, delete, and_
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.queries import QueryConstructor
from app.models.operations import Operation
from app.models.sources import SourceRegister, Object, Field, Model
from app.models.tags import Tag


async def add_tags(
        tags_like_model: SourceRegister | Object | Field | Model | Operation | QueryConstructor,
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
        tags_like_model: SourceRegister | Object | Model | Field | Operation,
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


async def remove_redundant_tags(session: AsyncSession):
    tags = await session.execute(
        select(Tag)
        .options(
            load_only(Tag.id),
            joinedload(Tag.source_registries),
            joinedload(Tag.objects),
            joinedload(Tag.fields),
            joinedload(Tag.models),
            joinedload(Tag.operations),
            joinedload(Tag.queries)
        )
        .where(
            and_(
                ~Tag.source_registries.any(),
                ~Tag.objects.any(),
                ~Tag.models.any(),
                ~Tag.operations.any(),
                ~Tag.queries.any()
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
