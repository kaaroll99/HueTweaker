import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from database import model
from utils.color_format import format_color_label
from utils.color_parse import BLACK_HEX, NEAR_BLACK_HEX, fetch_color_representation, color_parser
from views.favorites import FAVORITES_LIMIT, FavoritesView, extract_favorite_colors
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)

DOCS_ADD = "commands/favorites-add"
DOCS_LIST = "commands/favorites-list"


class FavoritesCog(BaseCog):

    group = app_commands.Group(name="favorites", description="Manage your personal favorite colors")

    @group.command(name="add", description="Add a color to your favorites (HEX code or CSS color name)")
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def add(self, interaction: discord.Interaction, color: str) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            parsed = color_parser(fetch_color_representation(interaction, color))
            if parsed is None:
                raise ValueError

            hex_value = NEAR_BLACK_HEX if parsed == BLACK_HEX else parsed
            display = format_color_label(hex_value)

            row = await self.db.select_one(model.Favorites, {"user_id": interaction.user.id})
            existing = extract_favorite_colors(row)

            if any(hex_value == hx.lower() for _, hx in existing):
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
            logger.info("%s[%s] issued bot command: /favorites add %s", interaction.user.name, interaction.locale, color)

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
