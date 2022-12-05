from fastapi import FastAPI
from app.logger_config import config_logger
from app.routers import db_mappings

config_logger()

app = FastAPI()
app.include_router(db_mappings.router, prefix='/mappings')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
