from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from app.config import settings
from app.errors import NoNeo4jConnection

driver = AsyncGraphDatabase.driver(settings.NEO4J_CONNECTION_STRING)


async def neo4j_session():
    async with driver.session() as session:
        try:
            yield session
        except (ServiceUnavailable, ValueError):
            raise NoNeo4jConnection(settings.NEO4J_CONNECTION_STRING)
