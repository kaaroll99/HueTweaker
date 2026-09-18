import datetime
import logging
import os
from typing import Optional

import discord
from discord import app_commands, Embed
from discord.ext import commands

from constants import BANNER_URL, DEV_GUILD_ID
from utils.migration import TOP_GUILDS_LIMIT, migrate_all

logger = logging.getLogger(__name__)


class DevCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.msg = bot.messages
        self.db = bot.db

    @app_commands.command(name="dev", description="Developer command. It won't work.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def dev(
        self,
        interaction: discord.Interaction,
        action: str,
        mode: Optional[str] = None,
        guild_id: Optional[str] = None,
    ) -> None:
        embed: Embed = discord.Embed(title=f"{self.bot.user.name}", description="",
                                     color=4539717, timestamp=datetime.datetime.now())
        await interaction.response.defer(ephemeral=True)
        file = None
        try:
            if interaction.guild_id == DEV_GUILD_ID:
                if action == "report":
                    import csv
                    os.makedirs('logs', exist_ok=True)
                    csv_file = os.path.join('logs', 'guilds_info.csv')
                    fields = ['Guild Name', 'Guild ID', 'Owner Name', 'Owner ID', 'Member Count', 'Preferred Locale']

                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fields)
                        writer.writeheader()

                        for guild in self.bot.guilds:
                            owner_name = guild.owner.name if guild.owner else "-"
                            owner_id = guild.owner.id if guild.owner else 0
                            writer.writerow({
                                'Guild Name': guild.name,
                                'Guild ID': guild.id,
                                'Owner Name': owner_name,
                                'Owner ID': owner_id,
                                'Member Count': guild.member_count,
                                'Preferred Locale': guild.preferred_locale
                            })
                    embed.description = f"Dane zapisano do pliku CSV: {csv_file}"
                    file = discord.File(csv_file)
                elif action == "tree":
                    await self.bot.tree.sync()
                    embed.description = "Command tree synchronization completed."
                elif action == "migrate":
                    embed.description = await self._start_migration(interaction, mode, guild_id)
                elif action == "stats":
                    import resource
                    import sys

                    api_latency = round(self.bot.latency * 1000, 2)
                    embed.add_field(name=":turtle: API Latency", value=f"{api_latency} ms", inline=False)

                    if self.bot.latencies:
                        shards_info = [f"Shard {shard_id}: {round(lat * 1000, 2)} ms" for shard_id, lat in self.bot.latencies]
                        embed.add_field(name=":turtle: Shards Latency", value="\n".join(shards_info), inline=False)

                    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    if sys.platform == "darwin":
                        usage_mb = usage / 1024 / 1024
                    else:
                        usage_mb = usage / 1024

                    embed.add_field(name=":brain: Max RAM Usage", value=f"{usage_mb:.2f} MB", inline=False)
                    embed.description = "Bot Statistics"
            else:
                embed.description = "Command for bot developers only."
        except discord.HTTPException as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)
        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
        finally:
            embed.set_footer(text=f"{self.bot.user.name} by kaaroll99", icon_url=self.bot.user.avatar)
            embed.set_image(url=BANNER_URL)

            if file:
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)

            logger.warning("%s[%s] issued bot command: /dev %s", interaction.user.name, interaction.locale, action)

    async def _start_migration(self, interaction: discord.Interaction, mode: Optional[str], guild_id: Optional[str]) -> str:
        """Kick off the legacy -> per-color role migration analysis in the background."""
        mode = (mode or "dry-run").strip().lower()
        if mode not in ("dry-run", "apply"):
            return "Unknown mode. Use `dry-run` (default) or `apply`."
        if mode == "apply":
            return "`apply` is not available in this build. Only the `dry-run` analysis is."

        target_guild_id: Optional[int] = None
        if guild_id:
            if not guild_id.strip().isdigit():
                return "guild_id must be a numeric Discord guild id."
            target_guild_id = int(guild_id.strip())
            if self.bot.get_guild(target_guild_id) is None:
                return f"Guild `{target_guild_id}` not found (bot is not a member or the shard is not ready)."

        scope = (
            f"guild `{target_guild_id}`" if target_guild_id
            else f"the top {TOP_GUILDS_LIMIT} guilds by member count (of {len(self.bot.guilds)})"
        )
        self.bot.loop.create_task(self._run_migration(interaction, False, target_guild_id))
        return (
            f"Migration started in **{mode}** mode for {scope}.\n"
            "The report will be posted here when finished and saved under `logs/`."
        )

    async def _run_migration(self, interaction: discord.Interaction, apply: bool, guild_id: Optional[int]) -> None:
        started = datetime.datetime.now()
        try:
            summary = await migrate_all(self.bot, apply=apply, guild_id=guild_id)
            text = summary.render()
        except Exception as e:
            logger.exception("Migration task crashed")
            text = f"Migration crashed: {e!r}"

        elapsed = datetime.datetime.now() - started
        text = f"{text}\n\nfinished in {elapsed.total_seconds():.1f}s"

        os.makedirs("logs", exist_ok=True)
        stamp = started.strftime("%Y%m%d_%H%M%S")
        path = os.path.join("logs", f"migration_{'apply' if apply else 'dry-run'}_{stamp}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.warning("Migration report saved to %s", path)

        try:
            if len(text) <= 1900:
                await interaction.followup.send(f"```\n{text}\n```", ephemeral=True)
            else:
                await interaction.followup.send(
                    f"Migration finished ({'apply' if apply else 'dry-run'}). Full report attached.",
                    file=discord.File(path),
                    ephemeral=True,
                )
        except discord.HTTPException as e:
            # Followup tokens expire after 15 minutes; the report is still on disk.
            logger.warning("Could not post migration report (%s); see %s", e, path)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DevCog(bot))
