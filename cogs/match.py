import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.color_format import ColorUtils, dominant_colors, format_color_label, harmony_colors
from utils.color_parse import color_parser, fetch_color_representation
from views.global_view import GlobalLayout
from views.match import MatchView

logger = logging.getLogger(__name__)

# 4 colors + the gradient button fill one row of 5 buttons.
MATCH_COLORS = 4


class MatchCog(BaseCog):

    @app_commands.command(name="match", description="Get username colors that match your avatar")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def match(self, interaction: discord.Interaction) -> None:
        docs_page = "commands/match"
        try:
            await interaction.response.defer(ephemeral=True)

            avatar = await interaction.user.display_avatar.replace(size=128, static_format="png").read()
            colors = await asyncio.to_thread(dominant_colors, avatar, MATCH_COLORS)
            if not colors:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['match_no_colors'], docs_page))
                return

            entries = [*colors, (colors[0], colors[1])] if len(colors) >= 2 else colors
            image = ColorUtils.generate_color_list_image(interaction.user.display_name, entries)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_match.png")
            view = MatchView(self.msg, self.msg['match_title'], self.bot, file, entries,
                             author_id=interaction.user.id, docs_page=docs_page)
            await interaction.followup.send(view=view, file=file, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "match", e)

        finally:
            logger.info("%s[%s] issued bot command: /match", interaction.user.name, interaction.locale)

    @app_commands.command(name="harmony", description="Get colors and gradients that go well with a color")
    @app_commands.describe(color="HEX (#9932f0), CSS name (royalblue), rgb/hsl/cmyk, random or @user")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def harmony(self, interaction: discord.Interaction, color: str) -> None:
        docs_page = "commands/harmony"
        try:
            await interaction.response.defer(ephemeral=True)
            hex_value = color_parser(await fetch_color_representation(interaction, self.db, color))
            if hex_value is None:
                raise ValueError
            base = int(hex_value, 16)
            complementary, left, right, *triadic = harmony_colors(base)
            if complementary == base:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['harmony_no_hue'], docs_page))
                return

            # Solid harmonies first (buttons 1-5), then the two gradients (6-7) on the second row.
            entries = [complementary, left, right, *triadic, (base, complementary), (left, right)]
            image = ColorUtils.generate_color_list_image(interaction.user.display_name, entries)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_harmony.png")
            description = self.msg['harmony_title'].format(format_color_label(base))
            view = MatchView(self.msg, description, self.bot, file, entries,
                             author_id=interaction.user.id, docs_page=docs_page, source="harmony")
            await interaction.followup.send(view=view, file=file, ephemeral=True)

        except ValueError:
            await self.respond(interaction, GlobalLayout(self.msg, self.msg['color_format'], docs_page))

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "harmony", e)

        finally:
            logger.info("%s[%s] issued bot command: /harmony %s", interaction.user.name, interaction.locale, color)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MatchCog(bot))
