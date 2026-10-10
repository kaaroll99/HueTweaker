"""One-time import of the command history from the bot logs into the analytics CSV files.

Run from the repository root: ``python -m analytics.import_logs [--dry-run] [--tz-offset HOURS]``.
Users are hashed by username, since the logs have no user ids.
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analytics.recorder import COLUMNS, WORKING_FILE, _first_month, load_salt, user_hash
from constants import HOLOGRAPHIC_COLORS
from utils.color_format import encode_style
from utils.color_parse import parse_static_style

MARKER = ".imported"
ROOT = Path(__file__).resolve().parents[1]
# The bot's own logs: today's app.log and the daily files the logger rotates into logs/history/.
LOG_DIR = ROOT / "logs"
DATA_DIR = ROOT / "analytics" / "data"

# Both log formats:
#   2025-03-01 00:20:38,152 - root - INFO - name[en-US] issued bot command: /set #fe33ed
#   2026-01-15 00:03:30,203Z INFO cogs.select [pid=1 tid=2] select:78 - name[en-US] issued bot command: /select
LINE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}Z?\s.* - (?P<user>[^\s\[\]]+)\[(?P<meta>[^\]]*)\] "
    r"(?P<msg>issued bot command: .*|selected palette color .*|applied favorite color .*"
    r"|restored color .* from history|applied color .* from /match)$"
)
MULTI_WORD = ("favorites add", "favorites list", "force set", "force remove", "force purge", "setup toprole", "setup select")
COLOR_COMMANDS = {"set", "gradient", "holographic", "force set"}
BUTTON_SOURCES = (("selected palette color ", "select"), ("applied favorite color ", "favorites"),
                  ("restored color ", "history"), ("applied color ", "match"))
HEX = re.compile(r"#?\b([0-9a-fA-F]{6})\b")
LOCALE = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,3})?$")


def _split_command(text: str) -> tuple[str, str]:
    """Split a logged command into its name (one or two words) and its arguments."""
    for name in MULTI_WORD:
        if text == name or text.startswith(name + " "):
            return name, text[len(name):].strip()
    name, _, args = text.partition(" ")
    return name, args.strip()


def _command_colors(name: str, args: str):
    """Return the style a logged color command set, or None when the line can't tell (random, @user)."""
    if name == "holographic":
        return HOLOGRAPHIC_COLORS
    if not args or args.lower() == "random" or "<@" in args:
        return None
    primary, _, secondary = args.partition(", ")
    try:
        colors, _ = parse_static_style(primary, secondary or None)
    except ValueError:
        return None
    return colors


def _button_colors(label: str):
    """Return the style named in a button log line (HEX codes or Holographic), or None."""
    if "holographic" in label.lower():
        return HOLOGRAPHIC_COLORS
    found = [int(h, 16) for h in HEX.findall(label)][:2]
    if not found:
        return None
    return found[0], (found[1] if len(found) > 1 else None), None


def log_files() -> list[Path]:
    files = sorted((LOG_DIR / "history").glob("*.log"))
    if (LOG_DIR / "app.log").exists():
        files.append(LOG_DIR / "app.log")
    return files


def parse_logs(files: list[Path], salt: bytes, tz_offset: int) -> tuple[list[list[str]], Counter]:
    """Return the analytics rows found in the logs, sorted by time, and counts per kind of line."""
    rows, stats = [], Counter()
    flagged: dict[str, datetime] = {}
    for path in files:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                m = LINE.match(line.rstrip("\n"))
                if not m:
                    continue
                at = datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S") - timedelta(hours=tz_offset)
                ts = at.strftime("%Y-%m-%dT%H:%M:%S")
                user, msg = m["user"], m["msg"]
                user_id = user_hash(salt, "name:" + user)
                locale = m["meta"] if LOCALE.match(m["meta"]) else ""

                if not msg.startswith("issued bot command: /"):
                    for prefix, source in BUTTON_SOURCES:
                        if msg.startswith(prefix):
                            colors = _button_colors(msg[len(prefix):])
                            if colors:
                                rows.append([ts, "color", source, "", user_id, encode_style(colors), locale])
                                stats["color"] += 1
                            break
                    continue

                name, args = _split_command(msg[len("issued bot command: /"):])
                if name.startswith("dev"):
                    stats["skipped /dev"] += 1
                    continue
                # A failed or blocked /set logs an extra line just before the normal one: not a second use.
                if args.endswith("(invalid format)") or args.startswith("(blocked"):
                    flagged[user] = at
                    stats["duplicate lines skipped"] += 1
                    continue
                rows.append([ts, "command", name, "", user_id, "", locale])
                stats["command"] += 1

                failed = user in flagged and (at - flagged.pop(user)).total_seconds() <= 2
                if name in COLOR_COMMANDS and not failed:
                    colors = _command_colors(name, args)
                    if colors:
                        rows.append([ts, "color", name, "", user_id, encode_style(colors), locale])
                        stats["color"] += 1
    rows.sort(key=lambda row: row[0])
    return rows, stats


def _existing_start(data_dir: Path) -> str | None:
    """Return the earliest timestamp already recorded, where the import has to stop."""
    earliest = None
    for path in data_dir.glob("*.csv"):
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if earliest is None or row["timestamp"] < earliest:
                    earliest = row["timestamp"]
    return earliest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=f"One-time import of the command history from the bot logs ({LOG_DIR}/history/*.log and app.log) "
                    f"into {DATA_DIR}.")
    parser.add_argument("--tz-offset", type=int, default=0,
                        help="hours to subtract from log times without a 'Z' if the server logged local time (default: 0)")
    parser.add_argument("--dry-run", action="store_true", help="only print what would be imported")
    args = parser.parse_args(argv)
    # The bot's color helpers read assets/ by relative path, like the bot itself.
    os.chdir(ROOT)

    data_dir = DATA_DIR
    files = log_files()
    if not files:
        sys.exit(f"No logs found in {LOG_DIR}/history or {LOG_DIR}/app.log.")
    print(f"Reading {len(files)} log file(s): {files[0].name} … {files[-1].name}")
    data_dir.mkdir(parents=True, exist_ok=True)
    if (data_dir / MARKER).exists():
        sys.exit(f"Already imported ({(data_dir / MARKER).read_text().strip()}). "
                 f"To redo it, delete the imported month files and {data_dir / MARKER}.")

    rows, stats = parse_logs(files, load_salt(data_dir), args.tz_offset)
    cutoff = _existing_start(data_dir)
    if cutoff:
        rows = [row for row in rows if row[0] < cutoff]
    if not rows:
        sys.exit("Nothing to import.")

    by_month: dict[str, list[list[str]]] = defaultdict(list)
    for row in rows:
        by_month[row[0][:7]].append(row)
    working_month = _first_month(data_dir / WORKING_FILE)
    targets = {month: data_dir / (WORKING_FILE if month == working_month else f"{month}.csv") for month in by_month}
    clashes = [p.name for month, p in targets.items() if p.exists() and month != working_month]
    if clashes:
        sys.exit(f"These files already exist, nothing was written: {', '.join(clashes)}")

    commands = Counter(row[2] for row in rows if row[1] == "command")
    print(f"{len(rows):,} events from {rows[0][0]} to {rows[-1][0]}" + (f" (stopped at {cutoff})" if cutoff else ""))
    print("  " + ", ".join(f"{k}: {v:,}" for k, v in stats.items()))
    print("  " + ", ".join(f"/{k}: {v:,}" for k, v in commands.most_common()))
    if args.dry_run:
        return

    for month, path in sorted(targets.items()):
        new_file = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(COLUMNS)
            writer.writerows(by_month[month])
    (data_dir / MARKER).write_text(json.dumps({
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "from": rows[0][0], "to": rows[-1][0],
        "events": len(rows), "files": sorted(p.name for p in targets.values()),
    }))
    print(f"Written {len(targets)} file(s) to {data_dir}")


if __name__ == "__main__":
    main()
