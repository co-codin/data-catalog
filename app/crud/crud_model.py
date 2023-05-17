from neo4j import AsyncSession
from app.crud.crud_source_registry import add_tags
from app.errors import ModelNameAlreadyExist
from app.models.model import Model
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload, load_only
from app.schemas.model import ModelIn


async def create_model(model_in: ModelIn, session: AsyncSession) -> str:
    model = Model(
        **model_in.dict(exclude={'tags'}),
    )
    await add_tags(model, model_in.tags, session)

    session.add(model)
    await session.commit()

    return model



async def check_on_model_uniqueness(name: str, session: AsyncSession):
    models = await session.execute(
        select(Model)
        .options(load_only(Model.name))
        .filter(
            Model.name == name
        )
    )
    models = models.scalars().all()
    for model in models:
        if models.name == name:
            raise ModelNameAlreadyExist(name)


