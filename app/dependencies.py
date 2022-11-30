from neo4j import GraphDatabase
from app.config import settings

driver = GraphDatabase.driver(settings.neo4j_connection_string)


def neo4j_session():
    with driver.session() as session:
        yield session
