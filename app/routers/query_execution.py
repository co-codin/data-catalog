import asyncio
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from starlette import status
from app.crud.crud_queries import set_query_status
from app.models.log import LogEvent, LogType
from app.models.queries import QueryExecution, QueryRunningPublishStatus, QueryRunningStatus
from app.dependencies import db_session, get_user, get_token
from sqlalchemy import update, select
from app.schemas.log import LogIn
import requests
from app.config import settings


from app.services.clickhouse import ClickhouseService
from app.services.log import add_log

router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)


@router.get('/{guid}', response_model=Dict[str, str])
async def get_query_execution_by_guid(guid: str, session=Depends(db_session), user=Depends(get_user)):
    query_execution = await session.execute(
        select(QueryExecution)
        .join(QueryExecution.query)
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

    return query_execution.dict()


@router.put('/{guid}')
async def update_query_status(guid: str, status: QueryRunningStatus, session=Depends(db_session)):
    await set_query_status(guid, status, session)



@router.put('/{guid}/publish', response_model=Dict[str, str])
async def publish_query_execution(
        guid: str, publish_name: str, force: bool = True, session=Depends(db_session), token=Depends(get_token)
):
    clickhouseService = ClickhouseService()
    clickhouseService.connect()
    clickhouseService.createPublishTable(guid)
    search_result = clickhouseService.getByName(guid, publish_name)

    if force:
        if len(search_result.result_set):
            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_name=publish_name,
                    publish_status=QueryRunningPublishStatus.PUBLISHING.value,
                )
            )
            success = await asyncio.get_running_loop().run_in_executor(
                None, send_publish, guid, force, token
            )
            publish_status = QueryRunningPublishStatus.PUBLISHED.value if success else QueryRunningPublishStatus.ERROR.value
            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_status=publish_status,
                )
            )
        else:

            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_status=QueryRunningPublishStatus.PUBLISHING.value,
                )
            )
            success = await asyncio.get_running_loop().run_in_executor(
                None, send_publish, guid, force, token
            )
            publish_status = QueryRunningPublishStatus.PUBLISHED.value if success else QueryRunningPublishStatus.ERROR.value
            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_status=publish_status,
                )
            )
    else:
        if len(search_result.result_set):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Publish name exists. Try change it')
        else:
            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_status=QueryRunningPublishStatus.PUBLISHING.value,
                )
            )
            success = await asyncio.get_running_loop().run_in_executor(
                None, send_publish, guid, force, token
            )
            publish_status = QueryRunningPublishStatus.PUBLISHED.value if success else QueryRunningPublishStatus.ERROR.value
            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_status=publish_status,
                )
            )


    return {"publish_name": publish_name, "publish_status": publish_name}


async def send_publish(guid: str, force: bool, token: str) -> dict[str, dict[str, str]]:
    response = requests.post(
        f'{settings.api_query_executor}/{guid}/publish',
        json={'force': force},
        headers={"Authorization": f"Bearer {token}"}
    )
    status = int(response.status_code())
    return status == 200