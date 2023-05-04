.. _roleplay:

========
RolePlay
========

This is the cog guide for the roleplay cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _roleplay-usage:

-----
Usage
-----

Set up a role play, where the author of messages are secret - the bot reposts all messages.

Admins can get started with ``[p]roleplay channel``, as well as some other configuration options.


.. _roleplay-commands:

--------
Commands
--------

.. _roleplay-command-roleplay:

^^^^^^^^
roleplay
^^^^^^^^

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]roleplay 

**Description**

Role play configuration.

This is a group command, so you can use it to configure the roleplay for a channel.

Get started with ``[p]roleplay channel``.

.. _roleplay-command-roleplay-channel:

""""""""""""""""
roleplay channel
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay channel [channel]

**Description**

Set the channel for the roleplay.

Leave blank to disable.

**Examples:**
- ``[p]roleplay channel`` - disable roleplay
- ``[p]roleplay channel #roleplay`` - set the channel to #roleplay

.. _roleplay-command-roleplay-delete:

"""""""""""""""
roleplay delete
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay delete [delete_after]

**Description**

Automatically delete messages in the role play channel after time has passed.

The time is in minutes.

The default is disabled.

**Examples:**
- ``[p]roleplay delete 5`` - delete after 5 mins
- ``[p]roleplay delete 30`` - delete after 30 mins
- ``[p]roleplay delete`` - disable deletion

.. _roleplay-command-roleplay-embed:

""""""""""""""
roleplay embed
""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay embed <embed>

**Description**

Enable or disable embeds.

The default is disabled.

**Examples:**
- ``[p]roleplay embed true`` - enable
- ``[p]roleplay embed false`` - disable

.. _roleplay-command-roleplay-log:

""""""""""""
roleplay log
""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay log [channel]

**Description**

Set a channel to log role play messages to.

If you do not specify a channel logging will be disabled.

**Examples:**
- ``[p]roleplay log #logs`` - set to a channel called logs
- ``[p]roleplay log`` - disable logging

.. _roleplay-command-roleplay-radio:

""""""""""""""
roleplay radio
""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay radio <radio>

**Description**

Enable or disable radio.

The default is disabled.

**Examples:**
- ``[p]roleplay radio true`` - enable radio mode
- ``[p]roleplay radio false`` - disable radio mode

.. _roleplay-command-roleplay-radiofooter:

""""""""""""""""""""
roleplay radiofooter
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay radiofooter [footer]

**Description**

Set a footer for radio mode (embed only)

This only applies to embeds.

**Example:**
- ``[p]roleplay radiofooter Transmission over``
- ``[p]roleplay radiofooter`` - reset to none

.. _roleplay-command-roleplay-radioimage:

"""""""""""""""""""
roleplay radioimage
"""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay radioimage [image_url]

**Description**

Set an image for radio mode (embed only)

This only applies to embeds.

**Example:**
- ``[p]roleplay radioimage https://i.imgur.com/example.png``
- ``[p]roleplay radioimage`` - reset to none

.. _roleplay-command-roleplay-radiotitle:

"""""""""""""""""""
roleplay radiotitle
"""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay radiotitle <title>

**Description**

Set a title for radio mode (embed only)

This only applies to embeds.

**Example:**
- ``[p]roleplay radiotitle New radio transmission detected`` - the default

.. _roleplay-command-roleplay-settings:

"""""""""""""""""
roleplay settings
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay settings 

**Description**

View the current settings for the roleplay.
