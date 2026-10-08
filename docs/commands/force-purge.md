---
description: Delete every HueTweaker color role on the server.
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

# force purge

{% hint style="danger" %}
Administrators only. This **can't be undone**: every member loses their color.
{% endhint %}

Delete every HueTweaker color role on the server. The bot asks for confirmation first, then reports how many roles were deleted.

**Syntax:** `/force purge`

**Good to know:**

* Only HueTweaker color roles are deleted: the ones the bot created and older ones named `color-<USER_ID>`. Other roles are never touched, even if their name starts with 🎨.
* Roles above the bot's highest role can't be deleted and are reported as failed.
* Cooldown: 10 seconds.

***

## Bot response

<div align="left"><figure><img src="../.gitbook/assets/image (10).png" alt="Purge confirmation"><figcaption></figcaption></figure></div>
