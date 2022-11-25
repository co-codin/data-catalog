from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from app.config import settings
from app.errors import NoNeo4jConnection

driver = GraphDatabase.driver(settings.NEO4J_CONNECTION_STRING)


def neo4j_session():
    with driver.session() as session:
        try:
            yield session
        except (ServiceUnavailable, ValueError):
            raise NoNeo4jConnection(settings.NEO4J_CONNECTION_STRING)
