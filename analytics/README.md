# Analytics (data collection)

The bot only collects usage data here. Charts and reports live in the separate private `huetweaker-analytics` repository, which copies `analytics/data/` from the bot's server (rsync) and shows it.

The repository holds only code. All data is git-ignored and stays on the server.

## Data

The bot writes events to `analytics/data/`:

- `working.csv`: the current month, appended every 60 s (and on shutdown).
- `YYYY-MM.csv`: past months. `working.csv` is renamed when the first event of a new month is written.
- `.salt`: random salt for user hashes, created on first start. Keep it, or the same user gets a new hash. It is not copied to the reporting machine.

One row per event:

| Column | Content |
| --- | --- |
| `timestamp` | UTC, `2026-09-01T20:04:16` |
| `event` | `command`, `color` or `blocked` |
| `name` | command (`set`, `favorites add`) or source of the change (`set`, `gradient`, `select`, `favorites`, `history`, `match`, `force set`) |
| `guild_id` | server id |
| `user` | salted SHA-256 of the user id (12 characters); the id itself is never stored |
| `value` | `color`: the style (`ff0000`, `ff5f6d+ffc371`, `a9c9ff+ffbbec+ffc3a0`); `blocked`: `set_limit`, `vote_required` or `gradient_unsupported` |
| `locale` | Discord client language (`en-US`, `pt-BR`, `es-419`…). Discord does not share the user's country; the language is the closest signal, and e.g. `en-US` is also used outside the US. |

`command` is recorded once a command finishes (cooldown and permission errors are not counted, `/dev` is skipped). `color` only when the color actually changed. The reporting repo reads this format; change both together.

## Importing the history from the logs (once)

`python3 -m analytics.import_logs` turns the `issued bot command` lines of `logs/history/*.log` and `logs/app.log` into the same CSV files, so the reports cover the time before the recorder existed. `--dry-run` only prints the counts.

- Both log formats are read (before and after 2025-08-18). Times without a `Z` are taken as UTC; `--tz-offset 2` if the server logged local time.
- A failed `/set` logs an extra `(invalid format)` / `(blocked …)` line; it is not counted as a second use (the log-based `stats.sh` counts it).
- The client language comes from the `name[en-US]` part of each line.
- Imported rows have no `guild_id` (not in the logs) and no `blocked` events; `user` is a hash of the username, so unique users across the import boundary are counted twice once. `color` rows are the colors typed into `/set`, `/gradient`, `/force set` and the palette / favorites / history buttons; a preview cancelled in the old logs can't be told apart.
- It stops at the first event already recorded by the bot, refuses to run twice (`analytics/data/.imported`), and never overwrites a month file.
