import logging

import discord
from discord.ext import commands

from cogs._base import BaseCog
from database import model
from utils.role_manager import TOPROLE_MODE_CUSTOM, TOPROLE_MODE_OFF, looks_like_color_role, remove_color_role
from views.welcome import WelcomeLayout

logger = logging.getLogger(__name__)


WELCOME_COMMANDS = ("setup toprole", "set", "match", "colors", "gradient", "holographic", "help")


def welcome_channel(guild: discord.Guild) -> discord.TextChannel | None:
    """The system channel, else the highest text channel the bot can write in."""
    candidates = [guild.system_channel] + sorted(guild.text_channels, key=lambda c: c.position)
    for channel in candidates:
        if channel is None:
            continue
        perms = channel.permissions_for(guild.me)
        if perms.view_channel and perms.send_messages:
            return channel
    return None


class JoinListenerCog(BaseCog):

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        """Fires for every leaver, cached or not (``chunk_guilds_at_startup=False``)."""
        user_id = payload.user.id
        guild = self.bot.get_guild(payload.guild_id)
        try:
            if guild is not None and await remove_color_role(self.db, guild, user_id, reason="HueTweaker: member left the server"):
                logger.info("Deleted color role of user %s who left guild %s", user_id, payload.guild_id)
            await self.db.delete(model.History, {"user_id": user_id, "guild_id": payload.guild_id})
            await self.db.delete(model.ColorRoles, {"user_id": user_id, "guild_id": payload.guild_id})
        except Exception as e:
            logger.warning("Cleanup after user %s left guild %s failed: %r", user_id, payload.guild_id, e)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """If the reference role of ``custom`` placement is deleted, fall back to ``off``."""
        if looks_like_color_role(role):
            return
        try:
            guild_obj = await self.db.select_one(model.Guilds, {"server": role.guild.id})
            if guild_obj and guild_obj.get("mode") == TOPROLE_MODE_CUSTOM and guild_obj.get("role") == role.id:
                await self.db.update(model.Guilds, {"server": role.guild.id}, {"mode": TOPROLE_MODE_OFF, "role": 0})
                logger.info("Reference role %s deleted in guild %s; placement mode reset to off", role.id, role.guild.id)
        except Exception as e:
            logger.warning("Could not check toprole reference after role %s was deleted: %r", role.id, e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        logger.info("Bot has been added to guild: %s", guild.name)
        channel = welcome_channel(guild)
        if channel is None:
            logger.info("No channel to send the welcome message to in guild %s", guild.id)
            return
        try:
            await channel.send(view=WelcomeLayout(await self.welcome_text(guild)),
                               allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as e:
            logger.warning("Could not send the welcome message in guild %s: %s", guild.id, e)

    async def welcome_text(self, guild: discord.Guild) -> str:
        mentions = {name.replace(" ", "_"): await self.mention(name) for name in WELCOME_COMMANDS}
        me = guild.me
        # Invited without permissions, the bot has no role of its own.
        role = f"**{me.display_name}**" if me.top_role.is_default() else me.top_role.mention
        warnings = ""
        if not me.guild_permissions.manage_roles:
            warnings += self.msg['welcome_no_manage_roles'].format(role=role)
        covering = [r for r in guild.roles if r > me.top_role and r.colour.value]
        if covering:
            warnings += self.msg['welcome_roles_above'].format(count=len(covering), role=role)
        extras = ""
        if "ENHANCED_ROLE_COLORS" in guild.features:
            extras = self.msg['welcome_gradients'].format(**mentions)
        return self.msg['welcome'].format(warnings=warnings, extras=extras, **mentions)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.info("Bot has been removed from guild: %s", guild.name)
        try:
            await self.db.delete_all(model.Guilds, {"server": guild.id})
            await self.db.delete_all(model.History, {"guild_id": guild.id})
            await self.db.delete_all(model.Select, {"server_id": guild.id})
            await self.db.delete_all(model.ColorRoles, {"guild_id": guild.id})
        except Exception as e:
            logger.warning("Cleanup after leaving guild %s failed: %r", guild.id, e)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
