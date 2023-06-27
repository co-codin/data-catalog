from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.log import Log, LogType, LogName, LogEvent
from app.schemas.log import LogIn


async def get_all_logs(session: AsyncSession):
    logs = await session.execute(
        select(Log).order_by(Log.id.desc())
    )
    logs = logs.scalars().all()
    if not logs:
        return logs

    return logs


async def create_log(session: AsyncSession, log_in: LogIn):
    log = Log(
        **log_in.dict()
    )

    session.add(log)
    return log


async def log_remove(session: AsyncSession, guid: str, author_guid: str, name: str, description: str):
    log_in = LogIn(
        type=LogType.DATA_CATALOG.value,
        log_name=name,
        text=LogName.REMOVE.value.format(guid),
        identity_id=author_guid,
        event=LogEvent.REMOVE.value,
        description=description
    )
    await create_log(session=session, log_in=log_in)
