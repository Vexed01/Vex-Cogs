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

.. _roleplay-command-roleplay-settings:

"""""""""""""""""
roleplay settings
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]roleplay settings 

**Description**

View the current settings for the roleplay.
