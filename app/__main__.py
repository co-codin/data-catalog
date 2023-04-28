import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.logger_config import config_logger
from app.routers import db_mappings, discovery, entities, sats, links, source_registry
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


@app.on_event('startup')
async def on_startup():
    await load_jwks()


@app.get("/health")
def health_check():
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
    uvicorn.run(app, host='0.0.0.0', port=settings.port)
