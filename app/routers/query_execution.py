from fastapi import APIRouter, Depends
from typing import Dict
from app.models.queries import QueryExecution
from app.dependencies import db_session, get_user
from sqlalchemy import update, select

from app.services.clickhouse import ClickhouseService

router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)


@router.put('/{guid}/publish', response_model=Dict[str, str])
async def publish_query_execution(
        guid: str, publish_name: str, publish_status: str, force: bool = True, session=Depends(db_session), _=Depends(get_user)
):
    query_execution = await session.execute(
        select(QueryExecution)
        .where(QueryExecution.guid == guid)
    )
    query_execution = query_execution.scalars().first()

    clickhouseService = ClickhouseService()
    clickhouseService.connect()
    clickhouseService.createPublishTable()
    search_result = clickhouseService.getByName(publish_name)

    if force:
        if len(search_result.result_set):
            clickhouseService.update(
                query_id=query_execution.query_id,
                dest_type=query_execution.desc_type,
                published_at=query_execution.publiches_at,
                publish_name=publish_name,
                publish_status=publish_status,
                status=publish_status,
                finished_at=query_execution.finished_at
            )

            await session.execute(
                update(QueryExecution)
                .where(QueryExecution.guid == guid)
                .values(
                    publish_name=publish_name,
                )
            )
        else:
            clickhouseService.insert(
                query_id=query_execution.query_id,
                dest_type=query_execution.dest_type,
                published_at=query_execution.published_at,
                publish_name=publish_name,
                publish_status=publish_status,
                status=publish_status,
                finished_at=query_execution.finished_at
            )
    else:
        if len(search_result.result_set):
            return 'Publish name exists. Try change it'
        else:
            clickhouseService.insert(
                query_id=query_execution.query_id,
                dest_type=query_execution.dest_type,
                published_at=query_execution.published_at,
                publish_name=publish_name,
                publish_status=publish_status,
                status=publish_status,
                finished_at=query_execution.finished_at
            )
