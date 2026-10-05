---
description: >-
  Get color information (HEX, RGB, HSL, CMYK). The command generates a color
  preview and CSS color names similar to the selected one.
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

Get color information and a preview image (HEX, RGB, HSL, CMYK). The command also returns up to several similar CSS color names.

**Parameters:**

* `<color>` - Color to inspect (required)

**Accepted color formats:**

* Hex (with or without #): F5DF4D or #F5DF4D
* CSS color names: royalblue
* Functional notation: rgb(...), hsl(...), cmyk(...)

**Username:**

* Mention another user to copy their color (e.g. @kaaroll99), or use "random".

**What the command returns:**

* Conversions: HEX, RGB, HSL, CMYK
* A small preview image of the color
* Up to 5 similar CSS color names (if available)

**Notes:**

* Invalid formats will trigger a helpful error message directing to the docs.
* The command is subject to a cooldown.

**Command syntax:**

* `/check <color>`

**Command examples:**

* `/check #F5DF4D`
* `/check royalblue`
* `/check rgb(245, 223, 77)`

***

## Bot response

<div align="left"><figure><img src="../.gitbook/assets/image (2).png" alt=""><figcaption></figcaption></figure></div>

