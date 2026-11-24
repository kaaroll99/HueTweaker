---
description: Show a color in HEX, RGB, HSL and CMYK, with a preview and similar color names.
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

# check

Show a color in HEX, RGB, HSL and CMYK, with a preview image and up to 5 similar CSS color names. Your color doesn't change.

**Syntax:** `/check <color>`

`<color>` can be any [color format](../main/colors.md#color-formats) except gradient presets. With `@user` you check that user's color.

**Examples:**

* `/check #F5DF4D`
* `/check royalblue`
* `/check rgb(245, 223, 77)`
* `/check @kaaroll99`

**Good to know:**

* On a server, **🎨 Set as my color** under the result sets the checked color as your username color. It works like [`/set`](set.md): you confirm a preview first, and it counts toward the free limit.
* Shortcut: right-click a member (or tap their profile on mobile) → **Apps** → **Check color** does the same as `/check @user`.
* Cooldown: 10 seconds.

***

## Bot response

<div align="left"><figure><img src="../.gitbook/assets/image (2).png" alt="Color information"><figcaption></figcaption></figure></div>
