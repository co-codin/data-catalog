import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.logger_config import config_logger
from app.routers import db_mappings, discovery, entities, sats, links, source_registry, keys, objects
from app.errors import APIError
from app.config import settings
from app.services.auth import load_jwks

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


@app.on_event('startup')
async def on_startup():
    await load_jwks()


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


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='localhost', port=settings.port)
