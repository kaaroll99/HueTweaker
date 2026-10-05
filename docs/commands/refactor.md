---
description: Rename old color-<USER_ID> roles to member names at once.
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

# refactor

{% hint style="warning" %}
The command can only be executed by a user with administrator privileges.
{% endhint %}

{% hint style="info" %}
This is a temporary command. It will be removed once most servers have switched to the new role names.
{% endhint %}

***

HueTweaker now names color roles after their member, e.g. `🎨 kaaroll99`, instead of `color-<USER_ID>`. Older roles are renamed automatically the next time their owner changes color. `/refactor` renames all of them on the server at once.

**What the command does:**

* Renames every `color-<USER_ID>` role to `🎨 <display name>` of its owner.
* Deletes old color roles whose owner has left the server.
* Reports how many roles were renamed, deleted, and could not be updated.

**Parameters:**

* This command takes no parameters.

**Notes:**

* The bot can only update roles below its own highest role. Move other roles below the bot's role and run the command again.
* On servers with many color roles it can take a few minutes.
* The command can be used once every 5 minutes per server.
* Colors and role positions don't change, and `/set` keeps working while the command runs.

**Command syntax:**

* `/refactor`

**Command examples:**

* `/refactor`
