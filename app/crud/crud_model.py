from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_source_registry import _get_authors_data_by_guids, _set_author_data, add_tags, update_tags
from app.errors.errors import ModelNameAlreadyExist
from app.models.model import Model, ModelVersion
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, load_only, joinedload
from app.schemas.model import ModelIn, ModelUpdateIn
import asyncio


async def create_model(model_in: ModelIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())

    model = Model(
        **model_in.dict(exclude={'tags'}),
        guid=guid,
    )
    await add_tags(model, model_in.tags, session)

    session.add(model)
    await session.commit()

    return guid



async def check_on_model_uniqueness(name: str, session: AsyncSession, guid: Optional[str] = None):
    models = await session.execute(
        select(Model)
        .options(load_only(Model.name))
        .filter(
            Model.name == name
        )
    )
    models = models.scalars().all()
    for model in models:
        if model.name == name and model.guid != guid:
            raise ModelNameAlreadyExist(name)


async def read_all(session: AsyncSession):
    models = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .order_by(Model.created_at)
    )
    models = models.scalars().all()

    return models


async def read_by_guid(guid: str, token: str, session: AsyncSession):
    model = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.comments))
        .options(joinedload(Model.model_versions))
        .filter(Model.guid == guid)
    )

    model = model.scalars().first()

    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if model.comments:
        author_guids = {comment.author_guid for comment in model.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, _get_authors_data_by_guids, author_guids, token
        )
        _set_author_data(model.comments, authors_data)

    return model


async def edit_model(guid: str, model_update_in: ModelUpdateIn, session: AsyncSession):
    model_update_in_data = {
        key: value for key, value in model_update_in.dict(exclude={'tags'}).items()
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
        .filter(Model.guid == guid)
    )
    model = model.scalars().first()
    if not model:
        return

    await update_tags(model, session, model_update_in.tags)

    session.add(model)
    await session.commit()



async def delete_by_guid(guid: str, session: AsyncSession):
    model = await session.execute(
        select(Model)
        .filter(Model.guid == guid)
    )
    model = model.scalars().first()

    await session.execute(
        delete(ModelVersion)
        .where(ModelVersion.model_id == model.id)
    )
    await session.execute(
        delete(Model)
        .where(Model.guid == guid)
    )
    await session.commit()