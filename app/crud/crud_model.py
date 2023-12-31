from datetime import datetime
import uuid
import asyncio

from typing import Optional
from fastapi import HTTPException, status

from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_access_label import add_access_label, update_access_label
from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import add_tags, update_tags

from app.errors.errors import ModelNameAlreadyExist
from app.models import LogType
from app.models.log import LogEvent
from app.models.models import Model, ModelVersion, ModelRelationOperation, ModelRelation, OperationBody, Operation
from app.schemas.log import LogIn
from app.schemas.model import ModelIn, ModelUpdateIn, ModelManyOut, ModelOut
from app.services.log import add_log


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
        .filter(Model.deleted_at == None)
        .order_by(Model.created_at)
    )
    models = models.scalars().all()
    return [ModelManyOut.from_orm(model) for model in models]


async def get_models_by_operation(guid: str, session: AsyncSession) -> list[ModelManyOut]:
    models = await session.execute(
        select(Model)
        .join(ModelVersion).join(ModelRelation).join(ModelRelationOperation).join(OperationBody).join(Operation)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.comments))
        .options(selectinload(Model.access_label))
        .filter(
            and_(
                Operation.guid == guid,
                Model.deleted_at == None
            )
        )
    )

    models = models.scalars().all()
    return [ModelManyOut.from_orm(model) for model in models]


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> ModelOut:
    model = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.comments))
        .options(selectinload(Model.access_label))
        .options(joinedload(Model.model_versions).selectinload(ModelVersion.tags))
        .options(joinedload(Model.model_versions).selectinload(ModelVersion.comments))
        .options(joinedload(Model.model_versions).selectinload(ModelVersion.access_label))
        .filter(
            and_(
                Model.deleted_at == None,
                Model.guid == guid
            )
        )
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

    model = await session.execute(
        select(Model)
        .options(selectinload(Model.tags))
        .options(selectinload(Model.access_label))
        .filter(
        and_(
            Model.deleted_at == None,
            Model.guid == guid
            )
        )
    )
    model = model.scalars().first()
    if not model:
        return

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


async def delete_by_guid(guid: str, session: AsyncSession, identity_id: str):
    model = await session.execute(
        select(Model)
        .filter(
            and_(
                Model.deleted_at == None,
                Model.guid == guid)
        )
    )
    model = model.scalars().first()

    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await add_log(session, LogIn(
        type=LogType.MODEL_CATALOG.value,
        log_name="Удаление модели",
        text="{{{name}}} {{{guid}}} удалена".format(
            name=model.name, 
            guid=model.guid
        ),
        identity_id=identity_id,
        event=LogEvent.DELETE_MODEL.value,
    ))

    await session.execute(
        update(Model)
        .where(Model.guid == guid)
        .values(
            deleted_at=datetime.utcnow(),
        )
    )
    await session.commit()
