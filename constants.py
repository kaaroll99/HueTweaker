BOT_ID = 1209187999934578738
DEV_GUILD_ID = 1135688599917056160

ACCENT_COLOR = 0xFCF5AB

DOCS_BASE_URL = "https://huetweaker.gitbook.io/docs"
BANNER_URL = "https://i.imgur.com/rXe4MHa.png"
INVITE_URL = (
    f"https://discord.com/api/oauth2/authorize"
    f"?client_id={BOT_ID}&permissions=1099981745184&scope=bot"
)
SUPPORT_SERVER_URL = "https://discord.gg/tYdK4pD6ks"
VOTE_URL = f"https://top.gg/bot/{BOT_ID}/vote"

# /set without a top.gg vote: this many color changes per rolling window, then vote or wait.
FREE_SET_USES = 2
FREE_SET_WINDOW = 30 * 60

# Discord's holographic role style: allowed only with exactly these primary, secondary and tertiary colors.
HOLOGRAPHIC_COLORS = (0xA9C9FF, 0xFFBBEC, 0xFFC3A0)

# Discord allows at most 250 roles per guild (HTTP 30005 when exceeded).
DISCORD_ROLE_LIMIT = 250
HTTP_MAX_ROLES_REACHED = 30005

# New color roles are named ``🎨 <display name>`` and bound to their owner in the ``color_roles`` table.
COLOR_ROLE_NAME_PREFIX = "🎨 "
DISCORD_ROLE_NAME_MAX = 100

COLOR_ROLE_PREFIX = "color-"
# Legacy color role: ``color-<user_id>``, recognized by name alone. Discord snowflakes are 15-20 digits
# (accounts from 2015 have 17-digit ids). Anchored on both ends: use ``fullmatch``/``match``.
COLOR_ROLE_PATTERN = r"^color-\d{15,20}$"
