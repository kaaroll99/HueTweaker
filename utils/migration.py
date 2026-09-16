"""Analysis of legacy per-user color roles (``color-<user_id>``).

Answers one question per guild: how many roles would a "one role per color" model save?
Report only; nothing is changed on Discord or in the database.

* ``legacy``   - roles matching ``color-<user_id>``
* ``orphans``  - legacy roles whose owner is no longer in the guild (would simply be deleted)
* ``colors``   - distinct colors (primary[+secondary]) among legacy roles with a present owner;
                 this is the number of roles the per-color model needs
* ``freed``    - ``legacy - colors`` (duplicates merged + orphans deleted)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import discord

from constants import COLOR_ROLE_PATTERN

logger = logging.getLogger(__name__)

_legacy_role_re = re.compile(COLOR_ROLE_PATTERN)


def role_colors_key(role: discord.Role) -> str:
    """Normalized color key: ``RRGGBB`` or ``RRGGBB+RRGGBB`` for gradients."""
    primary = role.color.value if role.color else 0
    key = f"{primary:06X}"
    if role.secondary_color:
        key += f"+{role.secondary_color.value:06X}"
    return key


@dataclass
class GuildMigrationReport:
    guild_id: int
    guild_name: str
    total_roles: int = 0
    legacy_roles: int = 0
    distinct_colors: int = 0
    orphans: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def merged(self) -> int:
        return max(0, self.legacy_roles - self.orphans - self.distinct_colors)

    @property
    def roles_freed(self) -> int:
        return self.legacy_roles - self.distinct_colors

    @property
    def roles_after(self) -> int:
        return self.total_roles - self.roles_freed

    @property
    def reduction_pct(self) -> float:
        return (self.roles_freed / self.legacy_roles * 100) if self.legacy_roles else 0.0

    def line(self) -> str:
        status = "ERR " if self.errors else "ok  "
        return (
            f"{status}{self.guild_name} ({self.guild_id}): roles {self.total_roles}->{self.roles_after} | "
            f"legacy={self.legacy_roles} colors={self.distinct_colors} merge={self.merged} orphan={self.orphans} "
            f"freed={self.roles_freed} ({self.reduction_pct:.0f}%)"
            + (f" | {'; '.join(self.errors)}" if self.errors else "")
        )


@dataclass
class MigrationSummary:
    apply: bool
    guilds: list[GuildMigrationReport] = field(default_factory=list)

    def total(self, attr: str) -> int:
        return sum(getattr(g, attr) for g in self.guilds)

    def render(self) -> str:
        touched = sorted((g for g in self.guilds if g.legacy_roles), key=lambda g: g.roles_freed, reverse=True)
        legacy, freed = self.total("legacy_roles"), self.total("roles_freed")
        pct = (freed / legacy * 100) if legacy else 0.0
        header = [
            f"Color role migration [{'APPLY' if self.apply else 'DRY-RUN'}]",
            f"guilds scanned: {len(self.guilds)}, guilds with legacy roles: {len(touched)}",
            f"legacy roles: {legacy}, distinct colors: {self.total('distinct_colors')}",
            f"merge (duplicates): {self.total('merged')}, orphans (owner left): {self.total('orphans')}",
            f"roles freed: {freed} of {legacy} ({pct:.0f}% reduction)",
            f"guilds with errors: {sum(1 for g in self.guilds if g.errors)}",
            "",
        ]
        return "\n".join(header + [g.line() for g in touched])


async def _owner_present(guild: discord.Guild, user_id: int) -> bool:
    if guild.get_member(user_id) is not None:
        return True
    try:
        await guild.fetch_member(user_id)
        return True
    except discord.NotFound:
        return False


async def analyze_guild(guild: discord.Guild) -> GuildMigrationReport:
    report = GuildMigrationReport(guild_id=guild.id, guild_name=guild.name)
    try:
        roles = await guild.fetch_roles()
    except discord.HTTPException as e:
        report.errors.append(f"fetch_roles failed: {e.code}")
        return report

    report.total_roles = len(roles)
    legacy_roles = [r for r in roles if _legacy_role_re.match(r.name)]
    report.legacy_roles = len(legacy_roles)
    if not legacy_roles:
        return report

    keys: set[str] = set()
    for role in legacy_roles:
        user_id = int(role.name.split("-", 1)[1])
        try:
            if await _owner_present(guild, user_id):
                keys.add(role_colors_key(role))
            else:
                report.orphans += 1
        except discord.HTTPException as e:
            report.errors.append(f"{role.name}: HTTP {e.code}")
            keys.add(role_colors_key(role))  # assume present: conservative estimate
    report.distinct_colors = len(keys)
    return report


async def migrate_all(bot, apply: bool, guild_id: Optional[int] = None) -> MigrationSummary:
    """Dry-run analysis only in this build; ``apply`` raises ``NotImplementedError``."""
    if apply:
        raise NotImplementedError("apply mode is not available in this build")

    summary = MigrationSummary(apply=False)
    guilds = [bot.get_guild(guild_id)] if guild_id else list(bot.guilds)
    for guild in guilds:
        if guild is None:
            summary.guilds.append(GuildMigrationReport(guild_id=guild_id or 0, guild_name="?", errors=["guild not found"]))
            continue
        try:
            report = await analyze_guild(guild)
        except Exception as e:
            report = GuildMigrationReport(guild_id=guild.id, guild_name=guild.name, errors=[repr(e)])
            logger.exception("Migration analysis failed for guild %s", guild.id)
        summary.guilds.append(report)
        if report.legacy_roles:
            logger.info("Migration [dry-run] %s", report.line())
    return summary
