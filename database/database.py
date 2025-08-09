from sqlalchemy import Table, Column, Integer, MetaData, BigInteger, Text
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
        """Create required tables if they do not exist."""
        if not self.__engine:
            raise Exception("Database is not connected. Call connect() first.")
        metadata = MetaData()
        # guilds table (legacy manual definition)
        Table(
            'guilds', metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('server', BigInteger),
            Column('role', BigInteger),
        )
        # select table for static colors
        Table(
            'select', metadata,
            Column('server_id', BigInteger, primary_key=True, nullable=False),
            Column('hex_1', Text),
            Column('hex_2', Text),
            Column('hex_3', Text),
            Column('hex_4', Text),
            Column('hex_5', Text),
            Column('hex_6', Text),
            Column('hex_7', Text),
            Column('hex_8', Text),
            Column('hex_9', Text),
            Column('hex_10', Text),
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

    def select_one(self, table, parameters=None):
        try:
            if not parameters:
                query = select(table).limit(1)
            else:
                where_clause = and_(*(getattr(table, k) == v for k, v in parameters.items()))
                query = select(table).where(where_clause).limit(1)

            result = self.__session.execute(query)
            row_obj = result.scalars().first()
            if not row_obj:
                return None
            return {column.key: getattr(row_obj, column.key) for column in row_obj.__table__.columns}
        except OperationalError:
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
