<div align="center">
    
![logo](https://github.com/user-attachments/assets/7db45e2e-c4d7-413d-8b42-c6ab34b84162)

![License](https://img.shields.io/github/license/kaaroll99/HueTweaker.svg?style=for-the-badge&logo=unlicense&logoColor=white)
![Servers](https://img.shields.io/badge/dynamic/json?url=https://discordbotlist.com/api/v1/bots/1209187999934578738&query=$.stats.guilds&style=for-the-badge&label=servers&color=5865F2&logo=serverless&logoColor=white)
![Servers](https://img.shields.io/badge/dynamic/json?url=https://discordbotlist.com/api/v1/bots/1209187999934578738&query=$.stats.users&style=for-the-badge&label=users&color=5865F2&logo=cilium&logoColor=white)
[![Invite the bot](https://img.shields.io/badge/Invite_the_bot-FE5F50?style=for-the-badge)](https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot)
[![Discord Application directory](https://img.shields.io/badge/Discord_App_directory-2b2d31?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/application-directory/1209187999934578738)
[![Gitbook docs](https://img.shields.io/badge/Gitbook_docs-BBDDE5?style=for-the-badge&logo=gitbook&logoColor=black)](https://huetweaker.gitbook.io/docs/)
</div>

The application allows users to manage the name color themselves with a single command.
The user can choose one of the predefined colors prepared on the server or set his own.
The application also includes several commands for administrators to customize the bot's operation for a specific server.

**Change the color of your username with a single command.**

- 🖌️ Set/change the username color using hex code or CSS color name.
- 🗂️ Create a list of predefined colors for users.
- 🗑️ Remove the username color.
- 🔎 Get color information (HEX, RGB, HSL, CMYK, Integer).
- ⚙️ Manage the color of a specific user's username.
- 💫 Set the top role for color roles

## User commands:
- `/help` - Information about the bot and a list of available commands.
- `/set` - Set/change the username color using hex code or CSS color name.
- `/select` - Choose one of the prepared colors on the server using the button under the message. 
- `/remove` - Remove the username color.
- `/check` - Color information (HEX, RGB, HSL, CMYK, Integer).

## Admin commands:
- `/force set` - Set/change the username color of the specific user using hex code or CSS color name.
- `/force remove` - Remove the username color of the specific user.
- `/force purge` - Removing all color roles.
- `/setup toprole` - Set the top role for color roles. All color roles will be set under the indicated role.
- `/setup select` - Configure the colors that will be available for selection using the `/select` command.
