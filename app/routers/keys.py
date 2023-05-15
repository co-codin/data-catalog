from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator

from sqlalchemy import select
from sqlalchemy.orm import load_only
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sources import SourceRegister
from app.services.crypto import encrypt, decrypt
from app.dependencies import db_session, get_user
from app.config import settings

router = APIRouter(prefix='/keys', tags=['keys'])


class KeyIn(BaseModel):
    old_key: str

    @validator('old_key')
    def key_must_be_hex(cls, v):
        bytes.fromhex(v)
        return v


@router.post('/rotate')
async def rotate(key_in: KeyIn, session: AsyncSession = Depends(db_session), _=Depends(get_user)):
    source_registries = await session.execute(
        select(SourceRegister)
        .options(load_only(SourceRegister.conn_string))
    )
    source_registries = source_registries.scalars().all()

    for source_registry in source_registries:
        decrypted_conn_string = decrypt(key_in.old_key, source_registry.conn_string)
        if decrypted_conn_string:
            encrypted_conn_string = encrypt(settings.encryption_key, decrypted_conn_string)
            source_registry.conn_string = encrypted_conn_string
            session.add(source_registry)
    await session.commit()
