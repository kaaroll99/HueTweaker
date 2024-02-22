# HueTweaker

Change the color of your username with a single command.

## User commands:
- `/help` - Information about the bot and a list of available commands
- `/color set` - Set the username color using hex code or CSS color name.
- `/color remove` - Remove the username color.
- `/color check` - Color information (HEX, RGB, HSL, CMYK, Integer).

## Admin commands:
- `/color forceset` - Set the username color of the specific user using hex code or CSS color name.
- `/color forceremove` - Remove the username color of the specific user.
- `/color toprole` - Set the top role for color roles. All color roles will be set under the indicated role.
- `/embed` - Embed generator that allows you to send embed messages based on JSON format.

JSON format example:
```json
{
    "title": "Your Title",
    "description": "Your description goes here.",
    "color": "454545",
    "image": "https://picsum.photos/200",
    "thumbnail": "https://picsum.photos/200",
    "author_name": "Bob",
    "author_url": "https://picsum.photos/200",
    "author_icon_url": "https://picsum.photos/200",
    "fields": [
        {
          "title": "Field 1",
          "value": "Value for Field 1",
          "inline": false
        },
        {
          "title": "Field 2",
          "value": "The maximum number of fields is 25",
          "inline": true
        }
    ],
    "footer_text": "Footer",
    "footer_icon": "https://picsum.photos/200"
}
```
