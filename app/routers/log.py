from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_token
from app.services.log import get_all_logs

router = APIRouter(
    prefix="/logs",
    tags=['log']
)


@router.get('/')
async def get_all(session=Depends(db_session), token=Depends(get_token)):
    return await get_all_logs(session, token)
