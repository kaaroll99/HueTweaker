---
description: Set/change the username color using hex code or CSS color name.
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

Set or change your username color. The color can be given as a HEX value (with or without a leading '#'), as a CSS color name, by copying another user's color (mention the user, e.g. @kaaroll99), or as "random" to pick a random color.

The command generates a preview image and asks for confirmation before applying the color.

**Parameters:**

* `<color>` - Color to set (required)

**Accepted color formats:**

* Hex: F5DF4D or #F5DF4D
* CSS color names: royalblue
* Other formats supported by the parser (e.g., rgb(...), hsl(...))

**Username:**

* Copy color from another user by mentioning them (e.g. @kaaroll99). If the selected user does not have a colored role an error will be returned.

**Notes:**

* If you don't already have a bot-managed color role, the bot will create one named `color-<YOUR_ID>` and assign it to you.
* To create a two-color gradient, use the `/gradient` command instead.
* The command is subject to a cooldown.

**Command syntax:**

* `/set <color>`

**Command examples:**

* `/set f5df4d`
* `/set royalblue`
* `/set @kaaroll99`
* `/set random`

***

## Bot response

<figure><img src="../.gitbook/assets/image (83).png" alt=""><figcaption></figcaption></figure>

<div align="left"><figure><img src="../.gitbook/assets/image.png" alt=""><figcaption></figcaption></figure></div>

