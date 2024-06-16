# HueTweaker

[![Invite the bot](https://img.shields.io/badge/Invite_the_bot-FE5F50?style=for-the-badge)](https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot)
[![Gitbook docs](https://img.shields.io/badge/Gitbook_docs-BBDDE5?style=for-the-badge&logo=gitbook&logoColor=black)](https://huetweaker.gitbook.io/docs/)
[![Discord Application directory](https://img.shields.io/badge/Discord_App_directory-2b2d31?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/application-directory/1209187999934578738)
[![Top.gg](https://img.shields.io/badge/Top.gg-FF3366?style=for-the-badge&logo=top.gg&logoColor=white)](https://top.gg/bot/1209187999934578738)
![License](https://img.shields.io/badge/license-gpl--3.0-f5df4d?style=for-the-badge&logo=unlicense&logoColor=white)

The application allows users to manage the name color themselves with a single command.
The user can choose one of the predefined colors prepared on the server or set his own.
The application also includes several commands for administrators to customize the bot's operation for a specific server.

<a href="https://top.gg/bot/1209187999934578738">
<img src="https://top.gg/api/widget/status/1209187999934578738.svg?noavatar=true" height="25">
</a>
<a href="https://top.gg/bot/1209187999934578738">
<img src="https://top.gg/api/widget/servers/1209187999934578738.svg?noavatar=true" height="25">
</a>

Change the color of your username with a single command.

- 🖌️ Set/change the username color using hex code or CSS color name.
- 🗂️ Create a list of predefined colors for users.
- 🗑️ Remove the username color.
- 🔎 Get color information (HEX, RGB, HSL, CMYK, Integer).
- ⚙️ Manage the color of a specific user's username.
- 💫 Set the top role for color roles
- 📋 JSON to Discord embed conversion.

### User commands:
- `/help` - Information about the bot and a list of available commands.
- `/set` - Set/change the username color using hex code or CSS color name.
- `/select` - Choose one of the prepared colors on the server using the button under the message. 
- `/remove` - Remove the username color.
- `/check` - Color information (HEX, RGB, HSL, CMYK, Integer).

### Admin commands:
- `/force set` - Set/change the username color of the specific user using hex code or CSS color name.
- `/force remove` - Remove the username color of the specific user.
- `/force purge` - Removing all color roles.
- `/setup toprole` - Set the top role for color roles. All color roles will be set under the indicated role.
- `/setup select` - Configure the colors that will be available for selection using the `/select` command.
- `/embed` - Embed generator that allows you to send embed messages based on JSON format.


### Embed JSON format example:
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
