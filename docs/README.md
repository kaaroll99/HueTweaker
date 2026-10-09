---
cover: .gitbook/assets/tlo.png
coverY: 0
layout:
  width: default
  cover:
    visible: true
    size: full
    mask: none
  title:
    visible: true
  description:
    visible: false
  tableOfContents:
    visible: true
  outline:
    visible: true
  pagination:
    visible: true
  metadata:
    visible: true
  tags:
    visible: true
  actions:
    visible: true
  anchors:
    visible: true
---

# HueTweaker

HueTweaker lets every member pick their own username color with one command. Admins can prepare a list of colors to choose from and decide where color roles sit in the role list.

<p align="center"><a href="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&#x26;permissions=1099981745184&#x26;scope=bot"><img src="https://img.shields.io/badge/Invite_the_bot-FE5F50?style=for-the-badge" alt="Invite the bot"></a> <a href="https://discord.com/application-directory/1209187999934578738"><img src="https://img.shields.io/badge/App_directory-2b2d31?style=for-the-badge&#x26;logo=discord&#x26;logoColor=white" alt="Discord Application directory"></a> <a href="https://top.gg/bot/1209187999934578738"><img src="https://img.shields.io/badge/Top.gg-FF3366?style=for-the-badge&#x26;logo=topdotgg&#x26;logoColor=white" alt="Top.gg"></a> </p>

![](https://img.shields.io/badge/dynamic/json?url=https://discordbotlist.com/api/v1/bots/1209187999934578738\&query=$.stats.guilds\&style=for-the-badge\&label=servers\&color=5865F2\&logoColor=white) ![](https://img.shields.io/badge/dynamic/json?url=https://discordbotlist.com/api/v1/bots/1209187999934578738\&query=$.stats.users\&style=for-the-badge\&label=users\&color=5865F2\&logoColor=white)

## Quick start

1. [Invite the bot](https://discord.com/api/oauth2/authorize?client_id=1209187999934578738\&permissions=1099981745184\&scope=bot).
2. **Admin:** in **Server Settings → Roles**, keep the **HueTweaker** role above other colored roles. Color roles go right below it ([`/setup toprole`](commands/setup-toprole.md) changes that).
3. **Everyone:** run [`/set`](commands/set.md) with a color, e.g. `/set royalblue`.

Right after joining, the bot posts these steps in the server's system channel (or the first channel it can write in) and warns if it lacks **Manage Roles** or if colored roles sit above its own role. For the first 24 hours `/set` has no free-use limit, so everyone can try colors.

Color not showing or an error? See [Troubleshooting](main/troubleshooting.md).

## Features

* 🖌️ Set your username color with a HEX code, CSS color name, rgb/hsl/cmyk, `random`, or copy it from another user ([color formats](main/colors.md#color-formats)).
* 🌈 Two-color gradients, ready-made gradient presets and the holographic style (need Server Boost and a [top.gg vote](main/voting.md)).
* 🖼️ Colors that match your avatar.
* 🗂️ A server color list members pick from.
* ⭐ Personal favorite colors and color history.
* 🔎 Color info: HEX, RGB, HSL, CMYK and similar color names.
* ⚙️ Admin tools: set or remove a member's color, choose where color roles sit.
