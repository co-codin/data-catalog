import asyncio
import json
import logging

import httpx

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import update, select
from sqlalchemy.orm import contains_eager

from psycopg import sql

from app.crud.crud_queries import set_query_status
from app.errors.query_exec_errors import QueryExecPublishNameAlreadyExist

from app.models.log import LogEvent, LogType
from app.models.queries import QueryExecution, QueryRunningStatus, QueryRunningPublishStatus
from app.mq import create_channel

from app.schemas.log import LogIn
from app.schemas.queries import PublishIn, QueryExecutionOut

from app.dependencies import db_session, get_user, get_token
from app.config import settings


from app.services.log import add_log

router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)

logger = logging.getLogger(__name__)


@router.get('/{guid}', response_model=QueryExecutionOut)
async def get_query_execution_by_guid(guid: str, session=Depends(db_session), user=Depends(get_user)):
    query_execution = await session.execute(
        select(QueryExecution)
        .join(QueryExecution.query)
        .options(contains_eager(QueryExecution.query))
        .where(QueryExecution.guid == guid)
    )
    query_execution = query_execution.scalars().first()

    if not query_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR.value,
            log_name="Результат запроса получен",
            text="Результат запроса {{{name}}} {{{guid}}} был получен".format(
                name=query_execution.query.name, 
                guid=query_execution.query.guid
            ),
            identity_id=user['identity_id'],
            event=LogEvent.GET_QUERY_RESULT.value
        ))

    return QueryExecutionOut.from_orm(query_execution)


@router.put('/{guid}')
async def update_query_status(guid: str, status: QueryRunningStatus, session=Depends(db_session)):
    await set_query_status(guid, status, session)


@router.put('/{guid}/publish')
async def publish_query_execution(
        guid: str,
        publish_in: PublishIn,
        session=Depends(db_session),
        token=Depends(get_token),
        user=Depends(get_user)
):
    if not publish_in.force:
        if await check_if_publish_table_exits(publish_in.publish_name, token):
            raise QueryExecPublishNameAlreadyExist(publish_in.publish_name)

    asyncio.create_task(send_to_publish(guid, publish_in.publish_name, user['identity_id']))
    await session.execute(
        update(QueryExecution)
        .where(QueryExecution.guid == guid)
        .values(publish_name=publish_in.publish_name, publish_status=QueryRunningPublishStatus.PUBLISHING.value)
    )


async def check_if_publish_table_exits(publish_name: str, token: str) -> bool:
    async with httpx.AsyncClient() as aclient:
        headers = {'Authorization': f'Bearer {token}'}
        response = await aclient.get(
            f'{settings.api_query_executor}/v1/publications/?publish_name={publish_name}',
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


async def send_to_publish(guid: str, publish_name: str, identity_id: str):
    data_to_send = {'publish_name': publish_name, 'identity_id': identity_id, 'guid': guid}
    async with create_channel() as channel:
        await channel.basic_publish(settings.publish_exchange, 'task', json.dumps(data_to_send))
