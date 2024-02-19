from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.exc import SAWarning


Base = declarative_base()


def scoreboard_class(table_name):
    class Scoreboard(Base):
        try:
            __tablename__ = table_name
            __table_args__ = {'extend_existing': True}
            id = Column('id', Integer, primary_key=True, autoincrement=True)
            name = Column('name', String)
            score = Column('score', Integer)
        except SAWarning as e:
            pass

    return Scoreboard

def list_class(table_name):
    class List(Base):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        id = Column('id', Integer, primary_key=True, autoincrement=True)
        name = Column('name', String)
    return List


def info_class(table_name):
    class Info(Base):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        id = Column('id', Integer, primary_key=True, autoincrement=True)
        guild_id = Column('guild_id', String)
        log_channel_id = Column('log_channel_id', String)
    return Info


