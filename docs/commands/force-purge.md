---
description: >-
  The command allows you to delete all roles with colors (created by HueTweaker)
  from the server.
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

# force purge

{% hint style="warning" %}
The command can only be executed by a user with administrator privileges.
{% endhint %}

{% hint style="danger" %}
The effect of the command is **irreversible** — execution at your own risk
{% endhint %}

Delete HueTweaker-created color roles from the server. The command opens a confirmation dialog before anything is deleted.

**Parameters:**

* This command takes no parameters.

**Notes:**

* The command targets color roles created by HueTweaker (`🎨 <display name>`) and older roles named `color-<USER_ID>` (e.g. `color-512674615223517205`).
* This operation is irreversible once confirmed.
* Requires administrator privileges.

**Command syntax:**

* `/force purge`

**Command examples:**

* `/force purge`

{% hint style="info" %}
HueTweaker keeps track of the color roles it created, so other roles are never deleted, even if their name starts with 🎨. Older roles are recognized by their `color-<USER_ID>` name.
{% endhint %}

<div align="left"><figure><img src="../.gitbook/assets/image (10).png" alt=""><figcaption></figcaption></figure></div>
