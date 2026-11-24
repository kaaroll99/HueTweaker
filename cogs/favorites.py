import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog, preset_choices
from core.database import model
from utils.color_format import decode_slots, format_colors_label
from utils.color_parse import parse_color_pair
from utils.favorites_manager import add_favorite
from views.favorites import FavoritesView
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
            key = await add_favorite(self.db, interaction.user.id, colors)
            await self.respond(interaction, GlobalLayout(self.msg, self.msg[key].format(format_colors_label(*colors)), DOCS_ADD))

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
            colors = decode_slots(row)

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FavoritesCog(bot))
