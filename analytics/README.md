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
| `event` | `command`, `color`, `blocked` or `guild` |
| `name` | command (`set`, `favorites add`), source of the change (`set`, `gradient`, `select`, `favorites`, `history`, `match`, `force set`), or for `guild`: `join` / `leave` |
| `guild_id` | server id |
| `user` | salted SHA-256 of the user id (12 characters); the id itself is never stored. Empty for `guild`. |
| `value` | `color`: the style (`ff0000`, `ff5f6d+ffc371`, `a9c9ff+ffbbec+ffc3a0`); `blocked`: `set_limit`, `vote_required` or `gradient_unsupported`; `guild`: `key=value` pairs joined by `;` (below) |
| `locale` | Discord client language; for `guild` the server's preferred language (`en-US`, `pt-BR`, `es-419`…). Discord does not share the user's country; the language is the closest signal, and e.g. `en-US` is also used outside the US. |

`guild` values (integers, booleans as `0`/`1`, an unknown value is empty):

- `join`: `members`, `boosted` (gradients available), `manage_roles` (the bot has the permission), `covered` (colored roles above the bot's role, which would hide member colors).
- `leave`: `members`, `age` (seconds since the bot joined; empty if unknown).

`command` is recorded once a command finishes (cooldown and permission errors are not counted, `/dev` is skipped). `color` only when the color actually changed. The reporting repo reads this format; change both together.

## Imported history

Months before the recorder existed were imported once from the `issued bot command` log lines. Those rows have no `guild_id` and no `blocked` events, and `user` is a hash of the username, so unique users across the import boundary are counted twice once. The import script was removed after use; it is in git history (`analytics/import_logs.py`).
