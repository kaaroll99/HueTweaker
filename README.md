# HueTweaker

 A simple discord bot that allows you to change the color of your username using the command.

## User commands:
- `/help` - Information about the bot and a list of available commands
- `/color set` - Setting the username color
- `/color remove` - Removing the username color
- `/color check` - Color information (HEX, RGB, HSL, CMYK, Integer)

## Admin commands
- `/color forceset` - Setting the username color of the specific user
- `/color forceremove` - Removing the username color of the specific user
- `/color toprole` - Set top role for color roles. All color roles will be set under the indicated role.
- `/embed` - Embed generator that allows you to send embed messages based on JSON format

JSON format example:
```json
{
  "title": "", 
  "description": "",
  "color": "454545",
  "image": "url_here",
  "thumbnail": "url_here",
  "author_name": "",
  "author_url": "url_here",
  "author_icon_url": "url_here",
  "fields": [
    {
      "title": "",
      "value": "",
      "inline": false
    },
    {
      "title": "",
      "value": "",
      "inline": false
    }
  ]
}
```