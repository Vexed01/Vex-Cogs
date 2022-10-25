.. _cmdlog:

======
CmdLog
======

This is the cog guide for the cmdlog cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _cmdlog-usage:

-----
Usage
-----

Log command usage in a form searchable by user ID, server ID or command name.

The cog keeps an internal cache and everything is also logged to the bot's main logs under
``red.vex.cmdlog``, level INFO.

The internal cache is non persistant and subsequently is lost on cog unload,
including bot shutdowns. The logged data will last until Red's custom logging
rotator deletes old logs.


.. _cmdlog-commands:

--------
Commands
--------

.. _cmdlog-command-cmdlog:

^^^^^^
cmdlog
^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]cmdlog 

.. tip:: Alias: ``cmdlogs``

**Description**

View command logs.

Note the cache is limited to 100 000 commands, which is approximately 50MB of RAM

.. _cmdlog-command-cmdlog-cache:

""""""""""""
cmdlog cache
""""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog cache 

**Description**

Show the size of the internal command cache.

.. _cmdlog-command-cmdlog-channel:

""""""""""""""
cmdlog channel
""""""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog channel [channel]

**Description**

Set the channel to send logs to, this is optional.

Run the comand without a channel to stop sending.

**Example:**
    - ``[p]cmdlog channel #com-log`` - set the log channel to #com-log
    - ``[p]cmdlog channel`` - stop sending logs

.. _cmdlog-command-cmdlog-command:

""""""""""""""
cmdlog command
""""""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog command <command>

**Description**

Upload all the logs that are stored for a specific command in the cache.

This does not check it is a real command, so be careful. Do not enclose it in " if there
are spaces.

You can search for a group command (eg ``cmdlog``) or a full command (eg ``cmdlog user``).
As arguments are not stored, you cannot search for them.

**Examples:**
    - ``[p]cmdlog command ping``
    - ``[p]cmdlog command playlist``
    - ``[p]cmdlog command playlist create``

.. _cmdlog-command-cmdlog-content:

""""""""""""""
cmdlog content
""""""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog content <to_log>

**Description**

Set whether or not whole message content should be logged. Default false.

.. _cmdlog-command-cmdlog-full:

"""""""""""
cmdlog full
"""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog full 

**Description**

Upload all the logs that are stored in the cache.

.. _cmdlog-command-cmdlog-server:

"""""""""""""
cmdlog server
"""""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog server <server_id>

.. tip:: Alias: ``cmdlog guild``

**Description**

Upload all the logs that are stored for for a specific server ID in the cache.

**Example:**
    - ``[p]cmdlog server 527961662716772392``

.. _cmdlog-command-cmdlog-user:

"""""""""""
cmdlog user
"""""""""""

**Syntax**

.. code-block:: none

    [p]cmdlog user <user_id>

**Description**

Upload all the logs that are stored for a specific User ID in the cache.

**Example:**
    - ``[p]cmdlog user 418078199982063626``
