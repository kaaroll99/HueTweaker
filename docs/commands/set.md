---
description: Set your username color.
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

# set

{% hint style="info" icon="star" %}
Without a vote you can change your color **2 times per 30 minutes**. [Voting on top.gg](../main/voting.md) removes this limit for 12 hours.
{% endhint %}

Set or change your username color. The bot shows a preview and applies the color after you press **Accept**.

**Syntax:** `/set <color>`

`<color>` can be any [color format](../main/colors.md#color-formats): HEX, CSS name, rgb/hsl/cmyk, `random` or `@user`.

**Examples:**

* `/set f5df4d`
* `/set royalblue`
* `/set @kaaroll99`
* `/set random`

**Good to know:**

* The first time, the bot creates a role named `🎨 <your display name>`. The name updates every time you change your color.
* **Undo** in the result message brings back your previous color.
* Only accepted changes count toward the free limit. Cancelling or pressing **Undo** doesn't.
* Copying a user who has a gradient copies the whole gradient. That needs the same as [`/gradient`](gradient.md): Server Boost and a vote.
* For two colors, use [`/gradient`](gradient.md).
* Cooldown: 10 seconds.

***

## Bot response

<figure><img src="../.gitbook/assets/image (83).png" alt="Preview with Accept and Cancel"><figcaption></figcaption></figure>

<div align="left"><figure><img src="../.gitbook/assets/image.png" alt="Color set"><figcaption></figcaption></figure></div>
