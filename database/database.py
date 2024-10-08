from sqlalchemy import Table, Column, Integer, MetaData, BigInteger
from sqlalchemy import create_engine
from sqlalchemy import insert, select, update, delete, and_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self, url):
        self.__engine = create_engine(url)
        self.__Session = sessionmaker(autocommit=False, autoflush=False, bind=self.__engine)

    def __enter__(self):
        self.__session = self.__Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__session.close()

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
        try:
            if not parameters:
                query = select(table)
            else:
                where_clause = and_(*(getattr(table, k) == v for k, v in parameters.items()))
                query = select(table).where(where_clause)

            result = self.__session.execute(query)
            rows = [{column.key: getattr(row, column.key) for column in row.__table__.columns} for row in
                    result.scalars()]
            return rows

        except OperationalError as e:
            self.__session.rollback()
            return False

    def create(self, table, values):
        try:
            query = insert(table).values(**values)
            self.__session.execute(query)
            self.__session.commit()
            return True
        except OperationalError as e:
            self.__session.rollback()
            return False

    def update(self, table, criteria, values):
        try:
            query = (update(table)
                     .where(and_(*(getattr(table, k) == v for k, v in criteria.items())))
                     .values(**values))
            self.__session.execute(query)
            self.__session.commit()
            return True
        except OperationalError as e:
            self.__session.rollback()
            return False

    def delete(self, table, criteria):
        try:
            where_clause = and_(*(getattr(table, k) == v for k, v in criteria.items()))
            query = delete(table).where(where_clause)
            self.__session.execute(query)
            self.__session.commit()
            return True
        except OperationalError as e:
            self.__session.rollback()
            return False
