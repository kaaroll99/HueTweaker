from sqlalchemy import create_engine
from sqlalchemy import text, inspect, insert, select, update, delete, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy import Table, Column, Integer, String, MetaData, BigInteger
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
        self.__engine = create_engine(self.__url)

    def close(self):
        if self.__engine:
            self.__engine.dispose()

    def database_init(self):
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")
        else:
            metadata = MetaData()
            Table(
                'guilds', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('server', BigInteger),
                Column('role', BigInteger),
            )

            metadata.create_all(self.__engine)
            return True

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

