---
description: Get colors and gradients that go well with a color.
---

# harmony

Get colors that go well with a color you give, picked with color theory. The bot shows your name in each of them:

* **1** Complementary: the opposite color on the color wheel.
* **2-3** Analogous: the neighbours on both sides (30° away).
* **4-5** Triadic: the two colors that make an even triangle with yours (120° away).
* 🌈 **6** Gradient of your color and its complementary.
* 🌈 **7** Gradient of the two analogous colors.

Press a numbered button to set that color or gradient.

**Syntax:** `/harmony <color>`

`<color>` can be any [color format](../main/colors.md#color-formats) except gradient presets. With `@user` you get harmonies for that user's color.

**Examples:**

* `/harmony royalblue`
* `/harmony #F5DF4D`
* `/harmony @kaaroll99`

**Good to know:**

* The 🌈 gradient buttons need Server Boost and a [top.gg vote](../main/voting.md), like [`/gradient`](gradient.md). Solid colors are free.
* Only the hue changes, so the suggestions are as light and as saturated as your color.
* Gray, black and white have no hue, so they have no harmonies.
* Cooldown: 10 seconds.
