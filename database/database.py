import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import model

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, url):
        self.__engine = create_engine(url)
        self.__Session = sessionmaker(autocommit=False, autoflush=False, bind=self.__engine)

    def database_init(self):
        if not self.__engine:
            raise Exception("Database is not connected.")
        model.Base.metadata.create_all(self.__engine)
        return True

    @staticmethod
    def _to_dict(obj):
        return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}

    def select(self, table_class, parameters=None):
        """Select multiple records from the database."""
        session = self.__Session()
        try:
            query = session.query(table_class)
            if parameters:
                query = query.filter_by(**parameters)
            results = query.all()
            return [self._to_dict(r) for r in results]
        except Exception as e:
            session.rollback()
            logger.error("Select error: %s", e)
            return False
        finally:
            session.close()

    def select_one(self, table_class, parameters=None):
        """Select a single record from the database."""
        session = self.__Session()
        try:
            query = session.query(table_class)
            if parameters:
                query = query.filter_by(**parameters)
            obj = query.first()
            return self._to_dict(obj) if obj else None
        except Exception as e:
            session.rollback()
            logger.error("Select_one error: %s", e)
            return False
        finally:
            session.close()

    def create(self, table_class, values):
        """Create a new record in the database."""
        session = self.__Session()
        try:
            obj = table_class(**values)
            session.add(obj)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error("Create error: %s", e)
            return False
        finally:
            session.close()

    def update(self, table_class, criteria, values):
        """Update a record in the database."""
        session = self.__Session()
        try:
            obj = session.query(table_class).filter_by(**criteria).first()
            if not obj:
                return False
            for k, v in values.items():
                setattr(obj, k, v)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error("Update error: %s", e)
            return False
        finally:
            session.close()

    def delete(self, table_class, criteria):
        """Delete a record from the database."""
        session = self.__Session()
        try:
            obj = session.query(table_class).filter_by(**criteria).first()
            if not obj:
                return False
            session.delete(obj)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error("Delete error: %s", e)
            return False
        finally:
            session.close()
