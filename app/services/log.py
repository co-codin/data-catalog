from app.crud.crud_author import get_authors_data_by_guids
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.log import Log, LogType, LogText, LogEvent
from app.schemas.log import LogIn
import asyncio


async def get_all_logs(session: AsyncSession, token: str):
    logs = await session.execute(
        select(Log).order_by(Log.id.desc())
    )
    logs = logs.scalars().all()
    if not logs:
        return logs
    
    author_guids = {log.identity_id  for log in logs}
    
    authors_data = await asyncio.get_running_loop().run_in_executor(
        None, get_authors_data_by_guids, author_guids, token
    )

    set_log_author_data(logs, authors_data)

    return logs

async def set_log_author_data(logs: list, authors_data: dict[str, dict[str, str]]):
    for log in logs:
        if log.identity_id != 'Системное событие':
            log.author_first_name = authors_data[log.identity_id]['first_name']
            log.author_last_name = authors_data[log.identity_id]['last_name']
            log.author_middle_name = authors_data[log.identity_id]['middle_name']
            log.author_email = authors_data[log.identity_id]['email']

async def add_log(session: AsyncSession, log_in: LogIn):
    log = Log(
        **log_in.dict()
    )

    session.add(log)
    return log


async def log_remove(session: AsyncSession, guid: str, author_guid: str, name: str):
    log_in = LogIn(
        type=LogType.DATA_CATALOG.value,
        log_name=name,
        text=LogText.REMOVE.value.format(guid),
        identity_id=author_guid,
        event=LogEvent.REMOVE.value,
    )
    await add_log(session=session, log_in=log_in)
