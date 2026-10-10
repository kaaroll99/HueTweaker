"""Database tables.

Unique constraints are created only with a new table; on an existing database they are added by
hand (SQL in ``CHANGELOG.md``).
"""

from sqlalchemy import BigInteger, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Guilds(Base):
    """Per-server configuration: color role placement mode and the reference role."""

    __tablename__ = 'guilds'
    __table_args__ = (UniqueConstraint('server', name='uq_guilds_server'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    server: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[int] = mapped_column(BigInteger, default=0)
    mode: Mapped[str] = mapped_column(String(16), default='off')


class Select(Base):
    """Server palette for ``/select``: up to 10 styles in ``utils.color_format.encode_style`` format."""

    __tablename__ = 'server_selections'

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


class Favorites(Base):
    """A user's favorite styles, shared across servers, in ``encode_style`` format."""

    __tablename__ = 'favorites'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
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


class ColorRoles(Base):
    """Which role is a member's color role.

    The role name is cosmetic; this row is the binding. Legacy roles named ``color-<user_id>``
    have no row until their owner next changes color.
    """

    __tablename__ = 'member_color_roles'
    __table_args__ = (
        UniqueConstraint('guild_id', 'user_id', name='uq_member_color_roles_guild_user'),
        UniqueConstraint('role_id', name='uq_member_color_roles_role'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)


class History(Base):
    """Last 5 colors per user per guild.

    Each ``color_n`` is a packed value, see ``utils.history_manager.pack_color`` (solid colors
    are the plain 24-bit int).
    """

    __tablename__ = 'history'
    __table_args__ = (UniqueConstraint('user_id', 'guild_id', name='uq_history_user_guild'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    color_1: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_2: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_3: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_4: Mapped[int | None] = mapped_column(BigInteger, default=None)
    color_5: Mapped[int | None] = mapped_column(BigInteger, default=None)
