---
description: Choose where color roles sit in the role list, so other colored roles don't cover them.
layout:
  width: default
  title:
    visible: true
  description:
    visible: true
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

# setup toprole

{% hint style="warning" %}
Administrators only.
{% endhint %}

Choose where HueTweaker's color roles sit in the role list. Discord shows the color of a member's **highest colored role**, so color roles have to be above other colored roles to be visible.

**Syntax:** `/setup toprole <mode> [role_name]`

| Mode | Where color roles go |
| --- | --- |
| `auto` | As high as the bot can reach (just below the bot's highest role). **Recommended.** |
| `custom` | Directly below the role given in `role_name`. |
| `off` | At the bottom of the role list. **Default.** |

**Examples:**

* `/setup toprole auto`
* `/setup toprole custom @users-colors`
* `/setup toprole off`

Color roles move as soon as you run the command, and new ones are placed the same way.

## Custom mode

Use it to put color roles at a specific place, e.g. below staff roles.

1. Create a role, e.g. `@users-colors`, and place it below the bot's role.

<div align="left"><figure><img src="../.gitbook/assets/Bez nazwy-1 (1).png" alt="users-colors role placed below the bot role"><figcaption></figcaption></figure></div>

2. Run `/setup toprole custom @users-colors`.

<div align="left"><figure><img src="../.gitbook/assets/image (6).png" alt="Top role set"><figcaption></figcaption></figure></div>

3. Color roles move directly below `@users-colors`.

<div align="left"><figure><img src="../.gitbook/assets/image (31).png" alt="Color roles below users-colors"><figcaption></figcaption></figure></div>

If the chosen role is above the bot's highest role, the bot places color roles as high as it can instead. If the chosen role is deleted, the mode switches to `off`.

## Common problems

**The chosen role is above the bot.** The bot can only manage roles below its own highest role. Move the bot's role above the chosen role.

<div align="left"><figure><img src="../.gitbook/assets/image (32).png" alt="Chosen role above the bot role"><figcaption></figcaption></figure></div>

**A colored role is above the color roles.** Members with that role see its color instead of their HueTweaker color. Move that role below the color roles or remove its color.

<div align="left"><figure><img src="../.gitbook/assets/image (33).png" alt="Colored role above the color roles"><figcaption></figcaption></figure></div>

More fixes: [Troubleshooting](../main/troubleshooting.md).
