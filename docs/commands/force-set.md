---
description: Set or change another member's username color.
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
Administrators only.
{% endhint %}

Set or change another member's username color, solid or gradient. The color is applied right away, without a preview.

**Syntax:** `/force set <username> <color> [secondary_color]`

* `<username>`: the member.
* `<color>`: any [color format](../main/colors.md#color-formats), or a preset name (`sunset`, `holographic`).
* `[secondary_color]`: optional, makes a gradient.

**Examples:**

* `/force set @kaaroll99 f5df4d`
* `/force set @kaaroll99 royalblue tomato`

**Good to know:**

* No vote and no `/set` limit. A gradient still needs Server Boost.
* If the member has no color yet, the bot creates a `🎨 <display name>` role for them.
* **Undo** in the result message brings back the previous color.
* The change is saved in the member's [`/history`](history.md).
* Cooldown: 10 seconds.

***

## Bot response

<div align="left"><figure><img src="../.gitbook/assets/image (3).png" alt="Color set for a member"><figcaption></figcaption></figure></div>
