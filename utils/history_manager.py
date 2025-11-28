from database import model

async def update_history(db, user_id, guild_id, color):
    history_cls = model.history_class("history")
    history = await db.select_one(history_cls, {"user_id": user_id, "guild_id": guild_id})

    if history:
        new_values = {
            "color_1": color,
            "color_2": history.get("color_1"),
            "color_3": history.get("color_2"),
            "color_4": history.get("color_3"),
            "color_5": history.get("color_4")
        }
        await db.update(history_cls, {"user_id": user_id, "guild_id": guild_id}, new_values)
    else:
        new_values = {
            "user_id": user_id,
            "guild_id": guild_id,
            "color_1": color,
            "color_2": None,
            "color_3": None,
            "color_4": None,
            "color_5": None
        }
        await db.create(history_cls, new_values)
