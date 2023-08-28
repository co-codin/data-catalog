from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

from app.database.sqlalchemy import db_session as _db_session
from app.database.apache_age import ag_session as _ag_session
from app.mq import PikaChannel, create_channel

from app.services.auth import decode_jwt

bearer = HTTPBearer()


async def db_session():
    async with _db_session() as session:
        yield session


async def get_user(token=Depends(bearer)) -> dict:
    try:
        return await decode_jwt(token.credentials)
    except Exception:
        raise HTTPException(status_code=401)


async def get_token(token=Depends(bearer), _=Depends(get_user)) -> str:
    return token.credentials


def ag_session():
    with _ag_session() as session:
        yield session


async def mq_channel() -> PikaChannel:
    async with create_channel() as channel:
        yield channel
