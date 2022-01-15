.. _stattrack:

=========
StatTrack
=========

This is the cog guide for the stattrack cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _stattrack-usage:

--------------
Resource Usage
--------------

CPU usage depends on your bot size and host machine performance. Because this is Python, the cog
can (for the most part) only use one core. You can check the performance of the background loop
with `stattrackinfo`.

For disk usage, this cog uses around 150KB per day.
This is just around 50MB per year (the cog will NOT automatically delete old data so this will increase over time)
It uses an SQLite database that requires no extra setup.

RAM usage will be at least double disk usage and may spike to more when commands are used or the loop is active.


-----
Usage
-----

Track your bot's metrics and view them in Discord.

Commands will output as a graph.
Data can also be exported with ``[p]stattrack export`` into a few different formats.


.. _stattrack-commands:

--------
Commands
--------

.. _stattrack-command-stattrack:

^^^^^^^^^
stattrack
^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]stattrack 

**Description**

View my stats.

.. _stattrack-command-stattrack-channels:

""""""""""""""""""
stattrack channels
""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack channels [timespan=1d] [metrics]

**Description**

Get channel stats.

You can just run this command on its own to see all metrics,
or specify some metrics - see below.

**Arguments**

``[timespan]`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

``[metrics]`` The metrics to show.
Valid options: ``total``, ``text``, ``voice``, ``stage``, ``category``.
Defaults to all of them.

Note that ``total`` will count users multiple times if they share multiple servers with the
Red, while ``unique`` will only count them once.

**Examples:**
    - ``[p]stattrack servers 3w2d``
    - ``[p]stattrack servers 5d``
    - ``[p]stattrack servers all``

.. _stattrack-command-stattrack-commands:

""""""""""""""""""
stattrack commands
""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack commands [timespan=1 day, 0:00:00]

**Description**

Get command usage stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack commands 3w2d``
    - ``[p]stattrack commands 5d``
    - ``[p]stattrack commands all``

.. _stattrack-command-stattrack-export:

""""""""""""""""
stattrack export
""""""""""""""""

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]stattrack export 

**Description**

Export stattrack data.

.. _stattrack-command-stattrack-export-csv:

""""""""""""""""""""
stattrack export csv
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack export csv 

**Description**

Export as CSV

.. _stattrack-command-stattrack-export-json:

"""""""""""""""""""""
stattrack export json
"""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack export json 

**Description**

Export as JSON with pandas orient "split" 

.. _stattrack-command-stattrack-latency:

"""""""""""""""""
stattrack latency
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack latency [timespan=1 day, 0:00:00]

.. tip:: Alias: ``stattrack ping``

**Description**

Get my latency stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack latency 3w2d``
    - ``[p]stattrack latency 5d``
    - ``[p]stattrack latency all``

.. _stattrack-command-stattrack-looptime:

""""""""""""""""""
stattrack looptime
""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack looptime [timespan=1 day, 0:00:00]

.. tip:: Aliases: ``stattrack time``, ``stattrack loop``

**Description**

Get my loop time stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack looptime 3w2d``
    - ``[p]stattrack looptime 5d``
    - ``[p]stattrack looptime all``

.. _stattrack-command-stattrack-messages:

""""""""""""""""""
stattrack messages
""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack messages [timespan=1 day, 0:00:00]

**Description**

Get message stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack messages 3w2d``
    - ``[p]stattrack messages 5d``
    - ``[p]stattrack messages all``

.. _stattrack-command-stattrack-servers:

"""""""""""""""""
stattrack servers
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack servers [timespan=1 day, 0:00:00]

.. tip:: Alias: ``stattrack guilds``

**Description**

Get server stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack servers 3w2d``
    - ``[p]stattrack servers 5d``
    - ``[p]stattrack servers all``

.. _stattrack-command-stattrack-status:

""""""""""""""""
stattrack status
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack status [timespan=1d] [metrics]

**Description**

Get status stats.

You can just run this command on its own to see all metrics,
or specify some metrics - see below.

**Arguments**

``[timespan]`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

``[metrics]`` The metrics to show. Valid options: ``online``, ``idle``, ``offline``, ``dnd``.
Defaults to all of them.

**Examples:**
    - ``[p]stattrack status`` - show all metrics, 1 day
    - ``[p]stattrack status 3w2d`` - show all metrics, 3 weeks 2 days
    - ``[p]stattrack status 5d dnd online`` - show dnd & online, 5 days
    - ``[p]stattrack status all online idle`` - show online & idle, all time

.. _stattrack-command-stattrack-system:

""""""""""""""""
stattrack system
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack system 

.. tip:: Alias: ``stattrack sys``

**Description**

Get system metrics.

.. _stattrack-command-stattrack-system-cpu:

""""""""""""""""""""
stattrack system cpu
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack system cpu [timespan=1 day, 0:00:00]

**Description**

Get CPU stats.

**Arguments**

<timespan> How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack system cpu 3w2d``
    - ``[p]stattrack system cpu 5d``
    - ``[p]stattrack system cpu all``

.. _stattrack-command-stattrack-system-mem:

""""""""""""""""""""
stattrack system mem
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack system mem [timespan=1 day, 0:00:00]

.. tip:: Aliases: ``stattrack system memory``, ``stattrack system ram``

**Description**

Get memory usage stats.

**Arguments**

<timespan> How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**
    - ``[p]stattrack system mem 3w2d``
    - ``[p]stattrack system mem 5d``
    - ``[p]stattrack system mem all``

.. _stattrack-command-stattrack-users:

"""""""""""""""
stattrack users
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack users [timespan=1d] [metrics]

**Description**

Get user stats.

You can just run this command on its own to see all metrics,
or specify some metrics - see below.

**Arguments**

``[timespan]`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

``[metrics]`` The metrics to show. Valid options: ``total``, ``unique``, ``humans``, ``bots``.
Defaults to all of them.

Note that ``total`` will count users multiple times if they share multiple servers with the
Red, while ``unique`` will only count them once.

**Examples:**
    - ``[p]stattrack users`` - show all metrics, 1 day
    - ``[p]stattrack users 3w2d`` - show all metrics, 3 weeks 2 days
    - ``[p]stattrack users 5d total unique`` - show total & unique, 5 days
    - ``[p]stattrack users all humans bots`` - show humans & bots, all time
