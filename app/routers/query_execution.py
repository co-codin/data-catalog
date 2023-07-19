from fastapi import APIRouter, Depends
from typing import Dict
from app.models.queries import QueryExecution
from app.dependencies import db_session, get_user
from sqlalchemy import update

router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)


@router.put('/{guid}/publish', response_model=Dict[str, str])
async def publish_query_execution(
        guid: str,  publish_name: str, session=Depends(db_session), _=Depends(get_user)
):
   await session.execute(
        update(QueryExecution)
        .where(QueryExecution.guid == guid)
        .values(
            publish_name=publish_name
        )
    )

