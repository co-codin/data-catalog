from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import db_mappings
from app.errors import APIError


app = FastAPI()
app.include_router(db_mappings.router, prefix='/mappings')


@app.exception_handler(APIError)
def api_exception_handler(request_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={'message': str(exc)}
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
