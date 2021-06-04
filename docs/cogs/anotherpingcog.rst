.. _anotherpingcog:

==============
AnotherPingCog
==============

This is the cog guide for the anotherpingcog cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _anotherpingcog-usage:

-----
Usage
-----

A rich embed ping command with latency timings.

You can customise the emojis, colours or force embeds with ``[p]pingset``.


.. _anotherpingcog-commands:

--------
Commands
--------

.. _anotherpingcog-command-ping:

^^^^
ping
^^^^

**Syntax**

.. code-block:: none

    [p]ping 

**Description**

A rich embed ping command with timings.

This will show the time to send a message, and the WS latency to Discord.
If I can't send embeds or they are disabled here, I will send a normal message instead.
The embed has more detail and is preferred.

.. _anotherpingcog-command-pingset:

^^^^^^^
pingset
^^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]pingset 

**Description**

Manage settings - emojis, embed colour, and force embed.

.. _anotherpingcog-command-pingset-forceembed:

""""""""""""""""""
pingset forceembed
""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]pingset forceembed 

**Description**

Toggle whether embeds should be forced.

If this is disabled, embeds will depend on the settings in ``embedset``.

If it's enabled, embeds will embeds will always be sent unless the bot doesn't
have permission to send them.

By default, this is True because the embed is richer and has more information.
And it looks looks better.

This will be removed when a global per-command settings is available in Core Red.

.. _anotherpingcog-command-pingset-green:

"""""""""""""
pingset green
"""""""""""""

**Syntax**

.. code-block:: none

    [p]pingset green <emoji> [hex_colour=default]

**Description**

Set the colour and emoji to use for the colour Green.

If you want to go back to the defaults, just do ``[p]pingset green default default``.

**Arguments:**

    ``<emoji>``
    Just send the emoji as you normally would. It must be a custom emoji and I must
    be in the sever the emoji is in.
    You can also put ``default`` to use 🟢

    ``[hex_colour]`` (optional)
    The hex code you want the colour for Red to be. It looks best when this is the
    same colour as the emoji. Google "hex colour" if you need help with this.

**Examples:**
    - ``[p]pingset green :emoji: #43B581``
    - ``[p]pingset green :emoji: default``
    - ``[p]pingset green default #43B581``
    - ``[p]pingset green default default``

.. _anotherpingcog-command-pingset-orange:

""""""""""""""
pingset orange
""""""""""""""

**Syntax**

.. code-block:: none

    [p]pingset orange <emoji> [hex_colour=default]

**Description**

Set the colour and emoji to use for the colour Orange.

If you want to go back to the defaults, just do ``[p]pingset orange default default``.

**Arguments:**

    ``<emoji>``
    Just send the emoji as you normally would. It must be a custom emoji and I must
    be in the sever the emoji is in.
    You can also put ``default`` to use 🟠

    ``[hex_colour]`` (optional)
    The hex code you want the colour for Red to be. It looks best when this is the
    same colour as the emoji. Google "hex colour" if you need help with this.

**Examples:**
    - ``[p]pingset orange :emoji: #FAA61A``
    - ``[p]pingset orange :emoji: default``
    - ``[p]pingset orange default #FAA61A``
    - ``[p]pingset orange default default``

.. _anotherpingcog-command-pingset-red:

"""""""""""
pingset red
"""""""""""

**Syntax**

.. code-block:: none

    [p]pingset red <emoji> [hex_colour=default]

**Description**

Set the colour and emoji to use for the colour Red.

If you want to go back to the defaults, just do ``[p]pingset red default default``.

**Arguments:**

    ``<emoji>``
    Just send the emoji as you normally would. It must be a custom emoji and I must
    be in the sever the emoji is in.
    You can also put ``default`` to use 🔴

    ``[hex_colour]`` (optional)
    The hex code you want the colour for Red to be. It looks best when this is the
    same colour as the emoji. Google "hex colour" if you need help with this.

**Examples:**
    - ``[p]pingset red :emoji: #F04747``
    - ``[p]pingset red :emoji: default``
    - ``[p]pingset red default #F04747``
    - ``[p]pingset red default default``

.. _anotherpingcog-command-pingset-settings:

""""""""""""""""
pingset settings
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]pingset settings 

**Description**

See your current settings.
