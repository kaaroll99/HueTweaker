---
description: >-
  Configure the colors that will be available for selection using the /select
  command.
---

# setup select

{% hint style="warning" %}
The command can only be executed by a user with administrator privileges.
{% endhint %}

{% hint style="danger" %}
The [setup-toprole.md](setup-toprole.md "mention") configuration is required for the command to work properly
{% endhint %}

Configure the static color list for the `/select` command. This opens an interactive panel where administrators can create the color list or add/edit entries.

**Behavior highlights:**

* The list supports up to 10 positions (stored as `hex_1` .. `hex_10`).
* If no colors exist yet you'll see a "Create color list" button; otherwise an "Add/Edit color on list" button is shown.
* Editing opens a form with two fields: the color index (1-10) and the color value (hex or CSS color name).
* Leaving the color value empty clears that entry.

**Notes:**

* Colors are parsed with the same rules as `/set` (hex or CSS names).
* The index must be an integer between 1 and 10.
* Requires administrator privileges.

**Command syntax:**

* `/setup select`

**Command examples:**

* `/setup select`

***

## Bot response

<figure><img src="../.gitbook/assets/image (82).png" alt=""><figcaption></figcaption></figure>

<div align="left"><figure><img src="../.gitbook/assets/image (9).png" alt=""><figcaption></figcaption></figure></div>

