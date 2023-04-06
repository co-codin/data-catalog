import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.logger_config import config_logger
from app.routers import db_mappings, discovery, entities, sats, links
from app.errors import APIError
from app.config import settings

config_logger()

logger = logging.getLogger(__name__)


app = FastAPI()
app.include_router(db_mappings.router, prefix='/mappings')
app.include_router(discovery.router, prefix='/discover')
app.include_router(entities.router, prefix='/hubs')
app.include_router(sats.router, prefix='/sats')
app.include_router(links.router, prefix='/links')


@app.middleware("http")
async def request_log(request: Request, call_next):
    """
    Global exception handler for catching non API errors.
    ALso catch, sort and write uvicorn output and critical errors to log
    :param request: Request
    :param call_next: call_next
    :return: JSONResponse
    """
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


@app.exception_handler(APIError)
def api_exception_handler(request_: Request, exc: APIError) -> JSONResponse:
    logger.warning(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={'message': str(exc)}
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app.__main__.app", host='0.0.0.0', port=settings.port, reload=settings.reload)
