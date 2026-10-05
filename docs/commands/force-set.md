---
description: >-
  Set/change the username color of the specific user using hex code or CSS color
  name.
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

# force set

{% hint style="warning" %}
The command can only be executed by a user with administrator privileges.
{% endhint %}

***

Set or change another user's username color. This command is for administrators and accepts the same input formats as `/set`: HEX (with or without #), CSS color names, mention a user to copy their color (e.g. @kaaroll99), or "random". You may also provide an optional secondary color to create a gradient.

**Parameters:**

* `<username>` - Name of the selected user (required)
* `<color>` - Primary color to set (required)
* `[secondary_color]` - Secondary color for gradient (optional)

**Accepted color formats:**

* Hex: F5DF4D or #F5DF4D
* CSS color names: royalblue
* Other formats supported by the parser (e.g., rgb(...), hsl(...))

**Notes:**

* If the target user doesn't have a bot-managed color role, the bot will create one named `🎨 <display name>` and assign it to the user.
* The vote requirements of `/set` and `/gradient` don't apply here. A gradient still needs the server's gradient support (Server Boost).
* Requires administrator privileges to run, and the bot must have permission to manage roles.

**Command syntax:**

* `/force set <username> <color> [secondary_color]`

**Command examples:**

* `/force set @kaaroll99 f5df4d`
* `/force set @kaaroll99 royalblue tomato`

***

## Bot response

<div align="left"><figure><img src="../.gitbook/assets/image (3).png" alt=""><figcaption></figcaption></figure></div>
