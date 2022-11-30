from pydantic import BaseSettings


class Settings(BaseSettings):
    NEO4J_CONNECTION_STRING: str = 'bolt://localhost:7687'


settings = Settings()
