from neo4j import AsyncSession
from app.crud.crud_source_registry import add_tags
from app.models.model import Model

from app.schemas.model import ModelIn


async def create_model(model_in: ModelIn, session: AsyncSession) -> str:
    model = Model(
        **model_in.dict(exclude={'tags'}),
    )
    await add_tags(model, model_in.tags, session)

    session.add(model)
    await session.commit()

    return model



