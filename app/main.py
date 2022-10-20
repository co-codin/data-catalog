from fastapi import FastAPI

from app.routers import db_mappings


app = FastAPI()
app.include_router(db_mappings.router, prefix='/mappings')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
