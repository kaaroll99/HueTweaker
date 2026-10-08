<div align="center">

![Servers](https://img.shields.io/badge/dynamic/json?url=https://discordbotlist.com/api/v1/bots/1209187999934578738&query=$.stats.guilds&style=for-the-badge&label=servers&color=5865F2&logoColor=white)
[![Invite the bot](https://img.shields.io/badge/Invite_the_bot-FE5F50?style=for-the-badge)](https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot)
[![Discord Application directory](https://img.shields.io/badge/Discord_App_directory-2b2d31?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/application-directory/1209187999934578738)
[![Gitbook docs](https://img.shields.io/badge/Gitbook_docs-BBDDE5?style=for-the-badge&logo=gitbook&logoColor=black)](https://huetweaker.gitbook.io/docs/)
![License](https://img.shields.io/github/license/kaaroll99/HueTweaker.svg?style=for-the-badge&logo=unlicense&logoColor=white)
![Last commit](https://img.shields.io/github/last-commit/kaaroll99/HueTweaker?style=for-the-badge&logo=github&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.7.1-5865F2?style=for-the-badge&logo=discord&logoColor=white&labelColor=2b2d31)
</div>




![logo](https://i.imgur.com/2x5Ga50.png)

## Set your username color with a single command

Give every member a **name color of their own**: HEX, CSS names, **gradients**, Discord's **holographic** style or random, set in seconds. Pick a server preset or create your own, with **no manual role management**. Add HueTweaker and let your community stand out.

## Features

💡 **Set up in seconds.** Native, intuitive **slash commands**. Members color their own name, with no roles to hand out by hand.

🖌️ **Colors & gradients.** Any **HEX code or CSS color name**, copy another member's color, blend two into a **gradient**, pick a ready-made **gradient preset**, or go **holographic**.

🖼️ **Match your avatar.** `/match` suggests colors (and a gradient) taken from your avatar.

🗂️ **Server list & favorites.** Offer up to **10 colors or gradients** in a visual menu, and let members save **10 personal favorites** (gradients too) to reuse anywhere.

⚙️ **Full admin control.** Set or purge any color and **configure the hierarchy** so color roles sit exactly where you want.

## Screenshots

![screenshots](https://i.imgur.com/IfP8BKV.png)

## Commands

### User commands

| Command | Description |
| --- | --- |
| `/help` | Bot info and the full command list. |
| `/set <color>` | Set your color: HEX, CSS name, copy a mention, `random` or a preset. |
| `/gradient <color> [secondary_color]` | Blend two colors into a gradient, or pick a preset (`/gradient sunset`). |
| `/holographic` | Discord's shimmering holographic style. |
| `/match` | Colors (and a gradient) that match your avatar. |
| `/select` | Pick a color or gradient from the server's list (with preview). |
| `/favorites add <color> [secondary_color]` | Save a color, gradient or preset to your personal list (up to 10, global). |
| `/favorites list` | Set a favorite with a button, or remove it via dropdown. |
| `/history` | View your last 5 colors and restore one with a button. |
| `/check <color>` | Show HEX/RGB/HSL/CMYK, similar names and a preview. |
| `/colors` | Browse gradient presets and CSS color names with HEX codes. |
| `/remove` | Remove your color. |

`/set`, `/gradient` and `/holographic` ask you to confirm a preview, and every color change comes with an **Undo to previous color** button. Gradients and holographic need Server Boost and a [top.gg vote](https://huetweaker.gitbook.io/docs/main/voting).

### Admin commands

| Command | Description |
| --- | --- |
| `/force set <user> <color> [secondary_color]` | Set another member's color (same formats as `/set`, optional gradient). |
| `/force remove <user>` | Remove a member's color. |
| `/force purge` | Remove HueTweaker-created color roles. |
| `/setup toprole <mode> [role]` | Choose where color roles sit in the hierarchy. |
| `/setup select` | Create or edit the server's list of colors and gradients. |

### Accepted color formats

| Format | Example |
| --- | --- |
| HEX (with or without `#`) | `F5DF4D`, `#F5DF4D` |
| CSS color name | `royalblue` |
| Functional notation | `rgb(245, 223, 77)`, `hsl(...)`, `cmyk(...)` |
| Copy from a member | `@kaaroll99` (copies the whole gradient, if they have one) |
| Random | `random` |
| Gradient preset | `sunset`, `ocean`, `holographic` (all in `/colors`) |

### Role placement (`/setup toprole`)

| Mode | Where color roles go |
| --- | --- |
| `auto` | As high as the bot can manage, just below its own top role. |
| `custom` | Directly below the chosen role (capped at what the bot can manage). |
| `off` | At the bottom of the role list (default). |

Full documentation: [huetweaker.gitbook.io/docs](https://huetweaker.gitbook.io/docs/)
