import age
import psycopg2

from contextlib import contextmanager

from app.config import settings


ag = age.connect(dsn=settings.age_connection_string)


@contextmanager
def ag_session() -> age.Age:
    try:
        check_on_conn_alive()
        yield ag
        ag.commit()
    except Exception as exc:
        ag.rollback()
        raise exc


def check_on_conn_alive():
    global ag
    try:
        with ag.connection.cursor() as cur:
            cur.execute("select 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        ag = age.connect(dsn=settings.age_connection_string)
    finally:
        with ag.connection.cursor() as cur:
            cur.execute("set schema 'ag_catalog'")
