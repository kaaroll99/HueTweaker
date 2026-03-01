from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Guilds(Base):
    __tablename__ = 'guilds'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    server: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[int] = mapped_column(BigInteger)


class Select(Base):
    __tablename__ = 'select'

    server_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    hex_1: Mapped[str | None] = mapped_column(Text, default=None)
    hex_2: Mapped[str | None] = mapped_column(Text, default=None)
    hex_3: Mapped[str | None] = mapped_column(Text, default=None)
    hex_4: Mapped[str | None] = mapped_column(Text, default=None)
    hex_5: Mapped[str | None] = mapped_column(Text, default=None)
    hex_6: Mapped[str | None] = mapped_column(Text, default=None)
    hex_7: Mapped[str | None] = mapped_column(Text, default=None)
    hex_8: Mapped[str | None] = mapped_column(Text, default=None)
    hex_9: Mapped[str | None] = mapped_column(Text, default=None)
    hex_10: Mapped[str | None] = mapped_column(Text, default=None)


class History(Base):
    __tablename__ = 'history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    color_1: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_2: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_3: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_4: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_5: Mapped[int | None] = mapped_column(BigInteger, default=None)
