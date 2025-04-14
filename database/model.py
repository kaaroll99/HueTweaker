from sqlalchemy import Column, BigInteger, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Guilds(Base):
    __tablename__ = 'guilds'
    __table_args__ = {'extend_existing': True}
    id = Column('id', BigInteger, primary_key=True, autoincrement=True)
    server = Column('server', BigInteger)
    role = Column('role', BigInteger)


def guilds_class(table_name):
    Guilds.__tablename__ = table_name
    return Guilds


class Select(Base):
    __tablename__ = 'select'
    __table_args__ = {'extend_existing': True}
    server_id = Column(BigInteger, primary_key=True, nullable=False)
    hex_1 = Column(Text)
    hex_2 = Column(Text)
    hex_3 = Column(Text)
    hex_4 = Column(Text)
    hex_5 = Column(Text)
    hex_6 = Column(Text)
    hex_7 = Column(Text)
    hex_8 = Column(Text)
    hex_9 = Column(Text)
    hex_10 = Column(Text)
    
    
def select_class(table_name):
    Select.__tablename__ = table_name
    return Select
