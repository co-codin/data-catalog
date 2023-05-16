from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.log import Log
from app.schemas.log import LogIn


async def get_all_logs(session: AsyncSession):
    logs = await session.execute(
        select(Log)
    )
    source_registries = source_registries.scalars().all()
    if not logs:
        return logs

    return logs


async def create_log(session: AsyncSession, log: LogIn):
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log