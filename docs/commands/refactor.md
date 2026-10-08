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
Administrators only.
{% endhint %}

{% hint style="info" %}
Temporary command. It will be removed once most servers have switched to the new role names.
{% endhint %}

Color roles used to be named `color-<USER_ID>`. Now they're named after their member, e.g. `🎨 kaaroll99`. Old roles are renamed when their owner changes color; `/refactor` renames all of them at once.

**Syntax:** `/refactor`

**What it does:**

* Renames every `color-<USER_ID>` role to `🎨 <display name>`.
* Deletes old color roles of members who left the server.
* Reports how many roles were renamed, deleted and skipped.

**Good to know:**

* Colors and role positions don't change, and `/set` keeps working meanwhile.
* The bot can only rename roles below its own highest role. Move the bot's role up and run it again.
* With many color roles it can take a few minutes.
* Cooldown: 5 minutes per server.
