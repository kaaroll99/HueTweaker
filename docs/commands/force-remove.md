---
description: Remove the username color of the specific user.
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

# force remove

{% hint style="warning" %}
The command can only be executed by a user with administrator privileges.
{% endhint %}

***

Remove another user's username color. The bot will remove/unassign the bot-managed color role from the selected user and delete that role if it exists. This command requires administrator privileges.

**Parameters:**

* `<username>` - Name of the selected user (required)

**Notes:**

* Only affects roles created and managed by the bot (`color-<USER_ID>`).
* Requires administrator privileges.

**Command syntax:**

* `/force remove <username>`

**Command examples:**

* `/force remove @kaaroll99`

***

## Bot response

<div align="left"><figure><img src="../.gitbook/assets/image (5).png" alt=""><figcaption></figcaption></figure></div>
