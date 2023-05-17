from typing import Optional
import uuid
from neo4j import AsyncSession
from app.crud.crud_source_registry import add_tags
from app.errors import ModelNameAlreadyExist
from app.models.model import Model
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload, load_only
from app.schemas.model import ModelIn


async def create_model(model_in: ModelIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())

    model = Model(
        **model_in.dict(exclude={'tags'}),
        guid=guid,
    )
    await add_tags(model, model_in.tags, session)

    session.add(model)
    await session.commit()

    return model.guid



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


