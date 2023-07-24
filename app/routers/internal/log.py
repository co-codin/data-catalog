from fastapi import APIRouter, Depends

from app.schemas.log import LogIn

from app.dependencies import db_session, get_user
from app.services.log import create_log

router = APIRouter(
    prefix="/internal/logs",
    tags=['internal log']
)


@router.post('/')
async def create_log(params: LogIn, session=Depends(db_session), _=Depends(get_user)):
    return await create_log(session)