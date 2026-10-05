---
description: >-
  Configure how HueTweaker positions color roles on the server — auto, off, or
  custom (directly below a chosen role). Proper configuration avoids color
  display problems.
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

# setup toprole

{% hint style="warning" %}
The command can only be executed by a user with administrator privileges.
{% endhint %}

***

## Usage

The command supports three modes:

* `auto` — moves color roles as high as the bot can manage.
* `off` — moves color roles to the bottom of the role list.
* `custom` — keeps color roles directly below the selected role.

The `[role_name]` parameter is only used with `custom`.

***

## Example

`/setup toprole auto`

`/setup toprole off`

`/setup toprole custom @colors`

***

## **Important**

* In `custom`, the chosen role is respected only up to the bot's own hierarchy.
* If the selected role is higher than the bot can manage, HueTweaker will place the color roles as high as possible instead.

## **What happens when you update the mode**

* The bot stores the selected mode for the server.
* Existing HueTweaker color roles are moved immediately to the new target position.

## Configuration (custom mode)

1. Create a toprole under the role that HueTweaker has so that it can manage it.

<div align="left"><figure><img src="../.gitbook/assets/Bez nazwy-1 (1).png" alt=""><figcaption></figcaption></figure></div>

2. Use `/setup` toprole custom with the `@users-colors` mention.

Bot response:

<div align="left"><figure><img src="../.gitbook/assets/image (6).png" alt=""><figcaption></figcaption></figure></div>

3. After getting this response, color roles are automatically moved under `@user-colors`.

<div align="left"><figure><img src="../.gitbook/assets/image (31).png" alt=""><figcaption></figcaption></figure></div>

If not all roles are transferred, use the command again.

### Role reset

To restore the default behavior, run `/setup toprole off` — color roles will be moved to the bottom of the role list. Use `/setup toprole auto` if you want the bot to keep them as high as possible automatically.

<div align="left"><figure><img src="../.gitbook/assets/image (7).png" alt=""><figcaption></figcaption></figure></div>

***

## Configuration issues

1. The bot can only manage roles below its own highest role. The example below shows a role layout that will cause `custom` mode to fall back (the chosen role is above the bot, so HueTweaker places the color roles as high as it can manage instead).

<div align="left"><figure><img src="../.gitbook/assets/image (32).png" alt=""><figcaption></figcaption></figure></div>

2. If roles are configured as in the screenshot below, users who have a role Some role with color will see its color instead of their individual color from HueTweaker.

<div align="left"><figure><img src="../.gitbook/assets/image (33).png" alt=""><figcaption></figcaption></figure></div>
