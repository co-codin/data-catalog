import asyncio
import json
import logging

from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.logger_config import config_logger
from app.mq import create_channel
from app.routers import (
    db_mappings, discovery, entities, model, model_version, sats, links, source_registry, keys, objects,
    model_data_type, model_quality, fields, model_relation_group, model_relation, model_resource,
    model_resource_attitude, operation, query_constructor
)
from app.errors import APIError
from app.config import settings
from app.services.auth import load_jwks
from app.services.synchronizer import update_data_catalog_data, process_graph_migration_failure

config_logger()

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(db_mappings.router)
app.include_router(discovery.router)
app.include_router(entities.router)
app.include_router(sats.router)
app.include_router(links.router)
app.include_router(source_registry.router)
app.include_router(keys.router)
app.include_router(objects.router)
app.include_router(model.router)
app.include_router(model_version.router)
app.include_router(model_data_type.router)
app.include_router(model_quality.router)
app.include_router(fields.router)
app.include_router(model_relation_group.router)
app.include_router(model_relation.router)
app.include_router(model_resource.router)
app.include_router(model_resource_attitude.router)
app.include_router(operation.router)
app.include_router(query_constructor.router)


@app.on_event('startup')
async def on_startup():
    await load_jwks()

    async with create_channel() as channel:
        await channel.exchange_declare(settings.migration_exchange, 'direct')

        await channel.queue_declare(settings.migration_request_queue)
        await channel.queue_bind(settings.migration_request_queue, settings.migration_exchange, 'task')

        await channel.queue_declare(settings.migrations_result_queue)
        await channel.queue_bind(settings.migrations_result_queue, settings.migration_exchange, 'result')

        asyncio.create_task(
            consume(settings.migrations_result_queue, update_data_catalog_data, process_graph_migration_failure)
        )


@app.middleware("http")
async def request_log(request: Request, call_next):
    try:
        response: Response = await call_next(request)
        if response.status_code < 400:
            logger.info(f"{request.method} {request.url} Status code: {response.status_code}")
        else:
            logger.warning(f"{request.method} {request.url} Status code: {response.status_code}")
        return response
    except Exception as exc:  # noqa
        logger.exception(str(exc))
        return JSONResponse(
            status_code=500,
            content={"message": "Something went wrong!"},
        )


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.exception_handler(APIError)
def api_exception_handler(request_: Request, exc: APIError) -> JSONResponse:
    logger.warning(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={'message': str(exc)}
    )


async def consume(query, func: Callable, failure_func: Callable):
    while True:
        try:
            logger.info(f'Starting {query} worker')
            async with create_channel() as channel:
                async for body in channel.consume(query):
                    try:
                        logger.info(f"Received message: {body}")
                        await func(body)
                    except Exception as e:
                        logger.exception(f'Failed to process message {body}: {e}')

                        if failure_func:
                            await failure_func(json.loads(body))
        except Exception as e:
            logger.exception(f'Worker {query} failed: {e}')

        await asyncio.sleep(0.5)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=settings.port)
