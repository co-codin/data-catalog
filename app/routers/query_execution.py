import asyncio

from fastapi import APIRouter, Depends


router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)
