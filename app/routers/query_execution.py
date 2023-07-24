from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
# import io
from starlette import status
# from starlette.responses import StreamingResponse


from app.models.queries import QueryExecution
from app.dependencies import db_session, get_user
from sqlalchemy import update, select
# import pandas as pd

from app.services.clickhouse import ClickhouseService

router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)

@router.get('/{guid}', response_model=Dict[str, str])
async def get_query_execution_by_guid(guid: str, session=Depends(db_session), _=Depends(get_user)):
    query_execution = await session.execute(
        select(QueryExecution)
        .where(QueryExecution.guid == guid)
    )
    query_execution = query_execution.scalars().first()

    if not query_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return query_execution.dict()


# router.get('/{guid}/download')
# async def download_uery_execution_by_guid(guid: str, session=Depends(db_session), _=Depends(get_user)):
#     query_execution = await session.execute(
#         select(QueryExecution)
#         .where(QueryExecution.guid == guid)
#     )
#     query_execution = query_execution.scalars().first()

#     if not query_execution:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
#     df = pd.DataFrame([query_execution.dict()])
#     stream = io.StringIO()
#     df.to_csv(stream, index=False)

#     response = StreamingResponse(
#         iter([stream.getvalue()]), media_type="text/csv")
#     response.headers["Content-Disposition"] = "attachment; filename=export.csv"
#     return response


@router.put('/{guid}/publish', response_model=Dict[str, str])
async def publish_query_execution(
        guid: str, publish_name: str, publish_status: str, force: bool = True, session=Depends(db_session), _=Depends(get_user)
):
    query_execution = await session.execute(
        select(QueryExecution)
        .where(QueryExecution.guid == guid)
    )
    query_execution = query_execution.scalars().first()

    if not query_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

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
                    publish_name=publish_name
                )
            )
            await clickhouseService.dropPublishTable(guid)
            clickhouseService.createPublishTable(guid)
            clickhouseService.insert(
                guid=guid,
                query_id=query_execution.query_id,
                published_at=query_execution.started_at.strftime("%m/%d/%Y, %H:%M:%S"),
                publish_name=publish_name,
                publish_status=publish_status,
                status=publish_status,
                finished_at=query_execution.finished_at.strftime("%m/%d/%Y, %H:%M:%S")
            )
        else:
            clickhouseService.insert(
                guid=guid,
                query_id=query_execution.query_id,
                published_at=query_execution.started_at.strftime("%m/%d/%Y, %H:%M:%S"),
                publish_name=publish_name,
                publish_status=publish_status,
                status=publish_status,
                finished_at=query_execution.finished_at.strftime("%m/%d/%Y, %H:%M:%S")
            )
    else:
        if len(search_result.result_set):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Publish name exists. Try change it')
        else:
            clickhouseService.insert(
                guid=guid,
                query_id=query_execution.query_id,
                published_at=query_execution.started_at.strftime("%m/%d/%Y, %H:%M:%S"),
                publish_name=publish_name,
                publish_status=publish_status,
                status=publish_status,
                finished_at=query_execution.finished_at.strftime("%m/%d/%Y, %H:%M:%S")
            )
    return {"publish_name": publish_name, "publish_status": publish_name}
