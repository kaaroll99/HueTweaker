---
description: Common problems and how to fix them.
---

# Troubleshooting

## My color doesn't show

Discord shows the color of your **highest colored role**. If another colored role is above your HueTweaker role, you see that color instead.

When this happens, the bot says so under the result and names the role that covers the color. An admin can fix it:

1. Run [`/setup toprole auto`](../commands/setup-toprole.md). Color roles move as high as the bot can reach.
2. If some colored roles are still above them, move the **HueTweaker** role higher in **Server Settings → Roles** and run `/setup toprole auto` again.

## "The bot does not have permissions to perform this operation"

The bot needs the **Manage Roles** permission and can only manage roles **below its own highest role**. In **Server Settings → Roles**, drag the **HueTweaker** role above the color roles, then try again.

## "This server has reached Discord's limit of 250 roles"

Each member with a color has their own role, and Discord allows at most 250 roles per server. Delete unused roles, or remove all color roles with [`/force purge`](../commands/force-purge.md).

## I can't change my color anymore

Without a vote, `/set` allows **2 changes per 30 minutes** (no limit during the first 24 hours after the bot joins a server). The bot shows when your next free change is available. [Voting on top.gg](voting.md) removes the limit for 12 hours.

## Gradients or holographic don't work

Gradients, presets and holographic need two things:

* **Server Boost.** Gradient role colors are a Discord boost perk. Without it, voting doesn't help.
* **A top.gg vote** from you. See [Voting](voting.md).

## "Incorrect color format or the selected user does not have the color set"

* Check the [color formats](colors.md#color-formats).
* When copying with `@user`, that user must have a HueTweaker color.

## I don't see the bot's commands

An admin may have limited them to certain roles or channels. See [Restricting commands](permissions.md).

## Still stuck?

Ask on the [support server](https://discord.gg/tYdK4pD6ks).
