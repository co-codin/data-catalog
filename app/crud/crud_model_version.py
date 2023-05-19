from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import ModelVersion
from app.schemas.model_version import ModelVersionIn


async def create_model_version(model_in: ModelVersionIn, session: AsyncSession) -> str:
    model_version = ModelVersion(
        **model_in.dict(),
    )

    session.add(model_version)
    await session.commit()

    return model_version.id

