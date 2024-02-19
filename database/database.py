from sqlalchemy import create_engine
from sqlalchemy import text, inspect, insert, select, update, delete, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy_utils import database_exists, create_database
from database import model


class Database:
    def __init__(self, url):
        self.__engine = None
        self.__url = url

    def __createsessions(self):
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")

        Session = sessionmaker(autocommit=False, autoflush=False, bind=self.__engine)
        session = Session()
        return session

    def connect(self):
        self.__engine = create_engine(self.__url, connect_args={"check_same_thread": False})

    def close(self):
        if self.__engine:
            self.__engine.dispose()

    def database_init(self):
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")

        if not database_exists(self.__url):
            create_database(self.__url)
            metadata = MetaData()

            Table(
                'guilds', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('server', Integer),
                Column('channel', Integer),
            )

            metadata.create_all(self.__engine)
            return True
        else:
            return False

    def check(self, guild_id: int):
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")

        inspector = inspect(self.__engine)

        if not inspector.has_table('guild_info') or not inspector.has_table('list_scoreboard'):
            return True
        else:
            return False

    def create_scoreboard(self, table_name):
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")

        metadata = MetaData()

        Table(
            table_name, metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String),
            Column('score', Integer)
        )

        inspector = inspect(self.__engine)

        if not inspector.has_table(table_name):
            metadata.create_all(self.__engine)
            return True
        else:
            return False

    def drop_table(self, table_name):
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")

        inspector = inspect(self.__engine)

        if inspector.has_table(table_name):
            table_to_drop = Table(table_name, MetaData())
            table_to_drop.drop(self.__engine)
            return True
        else:
            return False

    def select(self, table, parameters=None):
        if not table:
            raise AttributeError("Lack of required arguments.")

        session = self.__createsessions()
        try:
            if not parameters:
                query = select(table)
            else:
                where_clause = and_(*(getattr(table, k) == v for k, v in parameters.items()))
                query = select(table).where(where_clause)

            result = session.execute(query)
            rows = [{column.key: getattr(row, column.key) for column in row.__table__.columns} for row in result.scalars()]
            return rows
        except OperationalError as e:
            return False

    def create(self, table, values):
        if not table or not values:
            raise AttributeError("Lack of required arguments.")

        session = self.__createsessions()
        try:
            query = insert(table).values(**values)
            session.execute(query, values)
            session.commit()
            return True
        except OperationalError as e:
            return False

    def update(self, table, criteria, values):
        if not table or not criteria or not values:
            raise AttributeError("Lack of required arguments.")

        session = self.__createsessions()
        try:
            query = (update(table)
                     .where(and_(*(getattr(table, k) == v for k, v in criteria.items())))
                     .values(**values))

            combined_values = {**values, **criteria}
            session.execute(query, combined_values)
            session.commit()

            return True
        except OperationalError as e:
            return False

    def delete(self, table, criteria):
        if not table or not criteria:
            raise AttributeError("Lack of required arguments.")
        session = self.__createsessions()
        try:
            where_clause = and_(*(getattr(table, k) == v for k, v in criteria.items()))
            query = delete(table).where(where_clause)
            session.execute(query)
            session.commit()
            return True
        except OperationalError as e:
            return False

