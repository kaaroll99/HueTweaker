from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.exc import SAWarning

Base = declarative_base()


class Guilds(Base):
    __tablename__ = 'guilds'
    __table_args__ = {'extend_existing': True}
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    server = Column('server', Integer)
    role = Column('role', Integer)


def guilds_class(table_name):
    Guilds.__tablename__ = table_name
    return Guilds
