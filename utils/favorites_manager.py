"""Saving a personal favorite (``model.Favorites``), shared by ``/favorites add`` and the ⭐ result button."""

from core.database import model
from utils.color_format import SLOT_COUNT, Colors, decode_slots, encode_style


async def add_favorite(db, user_id: int, colors: Colors) -> str:
    """Save ``colors`` in the user's first free slot and return the ``messages.yml`` key of the outcome.

    ``favorites_added``, ``favorites_duplicate`` (already saved) or ``favorites_full`` (no free slot).
    """
    row = await db.select_one(model.Favorites, {"user_id": user_id})
    existing = decode_slots(row)
    if any(colors == saved for _, saved in existing):
        return 'favorites_duplicate'
    if not row:
        await db.create(model.Favorites, {"user_id": user_id, "hex_1": encode_style(colors)})
        return 'favorites_added'

    used_slots = {slot for slot, _ in existing}
    free_slot = next((i for i in range(1, SLOT_COUNT + 1) if i not in used_slots), None)
    if free_slot is None:
        return 'favorites_full'
    await db.update(model.Favorites, {"user_id": user_id}, {f"hex_{free_slot}": encode_style(colors)})
    return 'favorites_added'
