"""Analytics events buffered in memory and appended to monthly CSV files.

The CSV format (``COLUMNS``, ``working.csv`` renamed to ``YYYY-MM.csv`` when the month changes)
is a contract with the private ``huetweaker-analytics`` repo that reads these files. User ids
are stored only as salted hashes.
"""

import asyncio
import csv
import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

import discord

from utils.color_format import Colors, encode_style

logger = logging.getLogger(__name__)

# "locale" is the Discord client language (e.g. en-US, pt-BR); Discord does not expose a country.
COLUMNS = ["timestamp", "event", "name", "guild_id", "user", "value", "locale"]
WORKING_FILE = "working.csv"
FLUSH_INTERVAL = 60


class AnalyticsRecorder:
    """Collect events and write them every ``FLUSH_INTERVAL`` seconds; a no-op until ``start``."""

    def __init__(self) -> None:
        self._dir: Path | None = None
        self._salt = b""
        self._buffer: list[list[str]] = []
        self._task: asyncio.Task | None = None

    async def start(self, data_dir: str | Path) -> None:
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._salt = load_salt(self._dir)
        self._task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        """Stop the flush loop and write the events still in the buffer."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        await self.flush()

    def command(self, interaction: discord.Interaction, command: discord.app_commands.Command) -> None:
        if command.qualified_name != "dev":
            self._add("command", command.qualified_name, interaction, "")

    def color(self, interaction: discord.Interaction, source: str, colors: Colors) -> None:
        self._add("color", source, interaction, encode_style(colors))

    def blocked(self, interaction: discord.Interaction, source: str, reason: str) -> None:
        self._add("blocked", source, interaction, reason)

    def guild(self, name: str, guild: discord.Guild, **details) -> None:
        """Record a server ``join`` or ``leave``.

        There is no user. ``details`` become the value ``key=value;…`` (ints, empty for None) and
        the locale is the server's preferred one.
        """
        value = ";".join(f"{key}={'' if v is None else int(v)}" for key, v in details.items())
        self._append("guild", name, str(guild.id), "", value, guild.preferred_locale)

    def _add(self, event: str, name: str, interaction: discord.Interaction, value: str) -> None:
        self._append(event, name, str(interaction.guild_id or ""),
                     user_hash(self._salt, str(interaction.user.id)), value, interaction.locale)

    def _append(self, event: str, name: str, guild_id: str, user: str, value: str, locale) -> None:
        if self._dir is None:
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        locale = getattr(locale, "value", locale) or ""
        self._buffer.append([timestamp, event, name, guild_id, user, value, str(locale)])

    async def _flush_loop(self) -> None:
        while True:
            await asyncio.sleep(FLUSH_INTERVAL)
            await self.flush()

    async def flush(self) -> None:
        """Write the buffered events in a worker thread; on a write error they are dropped and logged."""
        if self._dir is None or not self._buffer:
            return
        rows, self._buffer = self._buffer, []
        try:
            await asyncio.to_thread(self._write, rows)
        except OSError as e:
            logger.warning("Analytics: could not write %d event(s): %s", len(rows), e)

    def _write(self, rows: list[list[str]]) -> None:
        """Append rows to the working file, rotating it whenever the month changes."""
        working = self._dir / WORKING_FILE
        working_month = _first_month(working)
        for month, group in groupby(rows, key=lambda row: row[0][:7]):
            if working_month and working_month != month:
                self._rotate(working, working_month)
            new_file = not working.exists()
            with working.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if new_file:
                    writer.writerow(COLUMNS)
                writer.writerows(group)
            working_month = month

    def _rotate(self, working: Path, month: str) -> None:
        """Move the working file's rows into ``<month>.csv``."""
        target = self._dir / f"{month}.csv"
        if not target.exists():
            working.rename(target)
            return
        # The month file already exists (e.g. events written after a rotation): append the rest.
        with working.open(newline="", encoding="utf-8") as src, target.open("a", newline="", encoding="utf-8") as dst:
            next(src, None)
            dst.writelines(src)
        working.unlink()


def load_salt(data_dir: Path) -> bytes:
    """Return the salt for user hashes, creating ``.salt`` (owner-only) on first use."""
    path = data_dir / ".salt"
    if not path.exists():
        path.write_text(secrets.token_hex(16))
        os.chmod(path, 0o600)
    return path.read_text().strip().encode()


def user_hash(salt: bytes, user_key: str) -> str:
    return hashlib.sha256(salt + user_key.encode()).hexdigest()[:12]


def _first_month(path: Path) -> str | None:
    """Return the ``YYYY-MM`` of the file's first event, or None for a missing or empty file."""
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        next(f, None)
        first = next(f, "")
    return first[:7] or None


recorder = AnalyticsRecorder()
