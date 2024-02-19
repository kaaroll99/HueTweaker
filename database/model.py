from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.exc import SAWarning


Base = declarative_base()


def guilds_class(table_name):
    class Guilds(Base):
        try:
            __tablename__ = table_name
            __table_args__ = {'extend_existing': True}
            id = Column('id', Integer, primary_key=True, autoincrement=True)
            server = Column('server', Integer)
            role = Column('role', Integer)
        except SAWarning as e:
            pass

    return Guilds


