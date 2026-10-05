# favorites add

Add a color to your personal favorites list. Favorites are saved to your account and are available on every server where HueTweaker is present (up to 10 colors). The color can be given as a HEX value (with or without a leading '#'), as a CSS color name, by copying another user's color (mention the user, e.g. @kaaroll99), or as "random".

**Parameters:**

* `<color>` - Color to add (required)

**Accepted color formats:**

* Hex: F5DF4D or #F5DF4D
* CSS color names: royalblue
* Other formats supported by the parser (e.g., rgb(...), hsl(...))

**Username:**

* Copy a color from another user by mentioning them (e.g. @kaaroll99).

**Notes:**

* The stored value is always a normalized HEX, regardless of the input format.
* Duplicate colors and a full list (10/10) are rejected with a message.
* Favorites are global to your account — the same on every server.

**Command syntax:**

* `/favorites add <color>`

**Command examples:**

* `/favorites add f5df4d`
* `/favorites add royalblue`
* `/favorites add random`

***

## Bot response

<figure><img src="../.gitbook/assets/image (78).png" alt=""><figcaption></figcaption></figure>
