from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_source_registry import add_tags
from app.errors import ModelNameAlreadyExist
from app.models.model import Model
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload, load_only
from app.schemas.model import ModelIn, ModelOut


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
    if not models:
        return models

    return models


async def read_by_guid(guid: str, session: AsyncSession):
    model = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .filter(Model.guid == guid)
    )

    model = model.scalars().first()

    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


    return model