import psycopg2

from sqlalchemy import create_engine
from sqlalchemy import URL
from sqlalchemy.dialects.postgresql import insert
from pluvisky.config.base import settings


class PgConfig: 
    def __init__(self):
        self.__database = settings.POSTGRES_DB
        self.__host = settings.POSTGRES_HOST
        self.__port = settings.POSTGRES_PORT
        self.__user = settings.POSTGRES_USER
        self.__pass = settings.POSTGRES_PASSWORD

    def client_connect_psycopg(self):
        conn = psycopg2.connect(
            database=self.__database,
            host=self.__host,
            user=self.__user,
            password=self.__pass,
            port=self.__port
        )
        return conn

    @staticmethod
    def insert_on_conflict_nothing(table, conn, keys, data_iter):
        data = [dict(zip(keys, row)) for row in data_iter]
        insert_statement = insert(table.table).values(data)
        conflict_update = insert_statement.on_conflict_do_update(
            constraint=f"{table.table.name}_pk",
            set_={column.key: column for column in insert_statement.excluded},
        )
        result = conn.execute(conflict_update)
        return result.rowcount
 
    def client_connect(self):
        url_object = URL.create(
            "postgresql",
            username=self.__user,
            password=self.__pass,
            host=self.__host,
            database=self.__database,
            port=self.__port
        )
        db = create_engine(url_object)
        return db.connect()
    