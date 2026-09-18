"""Per-user, per-guild history of the last 5 colors.

Each slot is one BigInteger. A solid color is stored as its plain 24-bit value, so rows written
before gradients existed still decode. A gradient is packed as
``primary | secondary << 24 | GRADIENT_FLAG`` (49 bits, fits a signed 64-bit column)."""

import logging

from database import model
from database.database import DatabaseError

logger = logging.getLogger(__name__)

HISTORY_SIZE = 5
_COLOR_MASK = 0xFFFFFF
GRADIENT_FLAG = 1 << 48


def pack_color(primary: int, secondary: int | None) -> int:
    if secondary is None:
        return primary & _COLOR_MASK
    return (primary & _COLOR_MASK) | ((secondary & _COLOR_MASK) << 24) | GRADIENT_FLAG


def unpack_color(value: int) -> tuple[int, int | None]:
    if value & GRADIENT_FLAG:
        return value & _COLOR_MASK, (value >> 24) & _COLOR_MASK
    return value & _COLOR_MASK, None


def history_colors(row: dict | None) -> list[tuple[int, int | None]]:
    """``[(primary, secondary), ...]`` newest first, skipping empty slots."""
    colors = []
    if row:
        for i in range(1, HISTORY_SIZE + 1):
            value = row.get(f"color_{i}")
            if value is not None:
                colors.append(unpack_color(int(value)))
    return colors


async def update_history(db, user_id: int, guild_id: int, primary: int, secondary: int | None = None) -> None:
    """Record the color as the newest history entry. History is best-effort: a database failure
    is logged and swallowed, because the color itself has already been applied."""
    try:
        await _update_history(db, user_id, guild_id, primary, secondary)
    except DatabaseError as e:
        logger.warning("History not updated for user %s in guild %s: %s", user_id, guild_id, e)


async def _update_history(db, user_id: int, guild_id: int, primary: int, secondary: int | None) -> None:
    packed = pack_color(primary, secondary)
    criteria = {"user_id": user_id, "guild_id": guild_id}
    history = await db.select_one(model.History, criteria)

    if history:
        if history.get("color_1") == packed:
            return  # already the most recent entry
        values = {"color_1": packed}
        for i in range(2, HISTORY_SIZE + 1):
            values[f"color_{i}"] = history.get(f"color_{i - 1}")
        await db.update(model.History, criteria, values)
    else:
        values = {**criteria, "color_1": packed}
        for i in range(2, HISTORY_SIZE + 1):
            values[f"color_{i}"] = None
        await db.create(model.History, values)
