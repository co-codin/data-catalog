import uuid
import asyncio

from typing import Optional
from fastapi import HTTPException, status

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_access_label import add_access_label, update_access_label
from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import add_tags, update_tags

from app.errors.errors import ModelNameAlreadyExist
from app.models.models import Model, ModelVersion
from app.schemas.model import ModelIn, ModelUpdateIn, ModelManyOut, ModelOut
from app.services.log import log_remove


async def create_model(model_in: ModelIn, session: AsyncSession) -> Model:
    guid = str(uuid.uuid4())

    model = Model(
        **model_in.dict(exclude={'tags', 'access_label'}),
        guid=guid,
    )
    await add_tags(model, model_in.tags, session)
    await add_access_label(model, model_in.access_label)

    session.add(model)
    return model


async def check_on_model_uniqueness(name: str, session: AsyncSession, guid: Optional[str] = None):
    models = await session.execute(
        select(Model)
        .where(Model.name == name)
    )
    models = models.scalars().all()
    for model in models:
        if model.name == name and model.guid != guid:
            raise ModelNameAlreadyExist(name)


async def read_all(session: AsyncSession) -> list[ModelManyOut]:
    models = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.comments))
        .options(selectinload(Model.access_label))
        .order_by(Model.created_at)
    )
    models = models.scalars().all()
    return [ModelManyOut.from_orm(model) for model in models]


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> ModelOut:
    model = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.comments))
        # .options(selectinload(Model.access_label))
        .options(joinedload(Model.model_versions).selectinload(ModelVersion.tags))
        .options(joinedload(Model.model_versions).selectinload(ModelVersion.comments))
        .options(joinedload(Model.model_versions).selectinload(ModelVersion.access_label))
        .filter(Model.guid == guid)
    )

    model = model.scalars().first()

    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    model_out = ModelOut.from_orm(model)

    if model.comments:
        author_guids = {comment.author_guid for comment in model.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(model_out.comments, authors_data)

    if model.model_versions:
        for idx, model_version in enumerate(model.model_versions):
            if model_version.comments:
                author_guids = {comment.author_guid for comment in model_version.comments}
                authors_data = await asyncio.get_running_loop().run_in_executor(
                    None, get_authors_data_by_guids, author_guids, token
                )
                set_author_data(model_out.model_versions[idx].comments, authors_data)

    return model_out


async def edit_model(guid: str, model_update_in: ModelUpdateIn, session: AsyncSession):
    model_update_in_data = {
        key: value for key, value in model_update_in.dict(exclude={'tags', 'access_label'}).items()
        if value is not None
    }

    await session.execute(
        update(Model)
        .where(Model.guid == guid)
        .values(
            **model_update_in_data,
        )
    )

    model = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.access_label))
        .filter(Model.guid == guid)
    )
    model = model.scalars().first()
    if not model:
        return

    await update_tags(model, session, model_update_in.tags)
    await update_access_label(model, model_update_in.access_label, session)

    session.add(model)
    await session.commit()


async def delete_by_guid(guid: str, session: AsyncSession, author_guid: str):
    await session.execute(
        delete(Model)
        .where(Model.guid == guid)
    )
    await session.commit()

    await log_remove(session=session, guid=guid, author_guid=author_guid, name="Удаление модели", description="")
