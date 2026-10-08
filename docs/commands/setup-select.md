---
description: Set up the color list for /select.
---

# setup select

{% hint style="warning" %}
Administrators only.
{% endhint %}

Set up the list of colors members can pick with [`/select`](select.md). Up to 10 colors.

**Syntax:** `/setup select`

**How to use:**

1. Run `/setup select`. The panel shows the current list.
2. Press **Create color list** (first time) or **Add/Edit color on list**.
3. Enter the position (1–10) and the color. Leave the color empty to clear that position.

**Good to know:**

* Colors can be HEX, CSS names or rgb/hsl/cmyk ([color formats](../main/colors.md#color-formats)). `random` and `@user` don't work here.
* Set [`/setup toprole`](setup-toprole.md) too, so other colored roles don't cover the colors.

***

## Bot response

<figure><img src="../.gitbook/assets/image (82).png" alt="Color list panel"><figcaption></figcaption></figure>

<div align="left"><figure><img src="../.gitbook/assets/image (9).png" alt="Edit color form"><figcaption></figcaption></figure></div>
