from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user
from app.filters.log import LogFilter
from app.services.log import get_all_logs
from fastapi_filter import FilterDepends

router = APIRouter(
    prefix="/logs",
    tags=['log']
)


@router.get('/')
async def get_all(session=Depends(db_session), _=Depends(get_user), user_filter: LogFilter = FilterDepends(LogFilter)):
    return await get_all_logs(session)
