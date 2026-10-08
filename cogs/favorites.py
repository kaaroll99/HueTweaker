import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog, preset_choices
from database import model
from utils.color_format import encode_style, format_colors_label
from utils.color_parse import parse_color_pair
from views.favorites import FAVORITES_LIMIT, FavoritesView, extract_favorite_colors
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)

DOCS_ADD = "commands/favorites-add"
DOCS_LIST = "commands/favorites-list"


class FavoritesCog(BaseCog):

    group = app_commands.Group(name="favorites", description="Manage your personal favorite colors")

    @group.command(name="add", description="Add a color, gradient or preset to your favorites")
    @app_commands.describe(
        color="Color (HEX, CSS name, rgb/hsl/cmyk, random, @user) or a preset (sunset, holographic)",
        secondary_color="Second color, to save a gradient (optional)",
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def add(self, interaction: discord.Interaction, color: str, secondary_color: str | None = None) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            colors, _ = await parse_color_pair(interaction, self.db, color, secondary_color)
            hex_value = encode_style(colors)
            display = format_colors_label(*colors)

            row = await self.db.select_one(model.Favorites, {"user_id": interaction.user.id})
            existing = extract_favorite_colors(row)

            if any(colors == saved for _, saved in existing):
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['favorites_duplicate'].format(display), DOCS_ADD))
                return

            if not row:
                await self.db.create(model.Favorites, {"user_id": interaction.user.id, "hex_1": hex_value})
            else:
                used_slots = {slot for slot, _ in existing}
                free_slot = next((i for i in range(1, FAVORITES_LIMIT + 1) if i not in used_slots), None)
                if free_slot is None:
                    await self.respond(interaction, GlobalLayout(self.msg, self.msg['favorites_full'], DOCS_ADD))
                    return
                await self.db.update(model.Favorites, {"user_id": interaction.user.id}, {f"hex_{free_slot}": hex_value})

            await self.respond(interaction, GlobalLayout(self.msg, self.msg['favorites_added'].format(display), DOCS_ADD))

        except ValueError:
            await self.respond(interaction, GlobalLayout(self.msg, self.msg['color_format'], DOCS_ADD))
            logger.info("%s[%s] issued bot command: /favorites add (invalid format)", interaction.user.name, interaction.user.id)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), DOCS_ADD))
            self.log_command_error(interaction, "favorites add", e)

        finally:
            log_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
            logger.info("%s[%s] issued bot command: /favorites add %s", interaction.user.name, interaction.locale, log_color)

    @add.autocomplete("color")
    async def add_color_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return preset_choices(current)

    @group.command(name="list", description="Show your favorite colors, set or remove one")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def favorites_list(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            row = await self.db.select_one(model.Favorites, {"user_id": interaction.user.id})
            colors = extract_favorite_colors(row)

            if not colors:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['favorites_no_colors'], DOCS_LIST))
                return

            view, file = FavoritesView.build(self.msg, self.bot, interaction.user.id, colors, interaction.user.display_name, DOCS_LIST)
            await interaction.followup.send(view=view, file=file, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), DOCS_LIST))
            self.log_command_error(interaction, "favorites list", e)

        finally:
            logger.info("%s[%s] issued bot command: /favorites list", interaction.user.name, interaction.locale)

    @add.error
    @favorites_list.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FavoritesCog(bot))
