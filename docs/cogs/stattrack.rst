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

-----
Usage
-----

BETA COG: StatTrack (Stat Tracking)


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

    [p]stattrack channels 

**Description**

See how many channels there are in all my guilds

.. _stattrack-command-stattrack-channels-categories:

"""""""""""""""""""""""""""""
stattrack channels categories
"""""""""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack channels categories [timespan=1 day, 0:00:00]

**Description**

Get categories stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack channels categories 3w2d``
``[p]stattrack channels categories 5d``
``[p]stattrack channels categories all``

.. _stattrack-command-stattrack-channels-stage:

""""""""""""""""""""""""
stattrack channels stage
""""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack channels stage [timespan=1 day, 0:00:00]

**Description**

Get stage channel stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack channels stage 3w2d``
``[p]stattrack channels stage 5d``
``[p]stattrack channels stage all``

.. _stattrack-command-stattrack-channels-text:

"""""""""""""""""""""""
stattrack channels text
"""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack channels text [timespan=1 day, 0:00:00]

**Description**

Get text channel stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack channels text 3w2d``
``[p]stattrack channels text 5d``
``[p]stattrack channels text all``

.. _stattrack-command-stattrack-channels-total:

""""""""""""""""""""""""
stattrack channels total
""""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack channels total [timespan=1 day, 0:00:00]

**Description**

Get total channel stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack channels total 3w2d``
``[p]stattrack channels total 5d``
``[p]stattrack channels total all``

.. _stattrack-command-stattrack-channels-voice:

""""""""""""""""""""""""
stattrack channels voice
""""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack channels voice [timespan=1 day, 0:00:00]

**Description**

Get voice channel stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack channels voice 3w2d``
``[p]stattrack channels voice 5d``
``[p]stattrack channels voice all``

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

``[p]stattrack commands 3w2d``
``[p]stattrack commands 5d``
``[p]stattrack commands all``

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

``[p]stattrack messages 3w2d``
``[p]stattrack messages 5d``
``[p]stattrack messages all``

.. _stattrack-command-stattrack-ping:

""""""""""""""
stattrack ping
""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack ping [timespan=1 day, 0:00:00]

**Description**

Get my ping stats.

Get command usage stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack ping 3w2d``
``[p]stattrack ping 5d``
``[p]stattrack ping all``

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

``[p]stattrack servers 3w2d``
``[p]stattrack servers 5d``
``[p]stattrack servers all``

.. _stattrack-command-stattrack-status:

""""""""""""""""
stattrack status
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack status 

**Description**

See stats about user's statuses.

.. _stattrack-command-stattrack-status-dnd:

""""""""""""""""""""
stattrack status dnd
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack status dnd [timespan=1 day, 0:00:00]

**Description**

Get dnd stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack status dnd 3w2d``
``[p]stattrack status dnd 5d``
``[p]stattrack status dnd all``

.. _stattrack-command-stattrack-status-idle:

"""""""""""""""""""""
stattrack status idle
"""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack status idle [timespan=1 day, 0:00:00]

**Description**

Get idle stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack status idle 3w2d``
``[p]stattrack status idle 5d``
``[p]stattrack status idle all``

.. _stattrack-command-stattrack-status-offline:

""""""""""""""""""""""""
stattrack status offline
""""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack status offline [timespan=1 day, 0:00:00]

**Description**

Get offline stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack status offline 3w2d``
``[p]stattrack status offline 5d``
``[p]stattrack status offline all``

.. _stattrack-command-stattrack-status-online:

"""""""""""""""""""""""
stattrack status online
"""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack status online [timespan=1 day, 0:00:00]

**Description**

Get online stats.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack status online 3w2d``
``[p]stattrack status online 5d``
``[p]stattrack status online all``

.. _stattrack-command-stattrack-storage:

"""""""""""""""""
stattrack storage
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack storage 

**Description**

See how much RAM and disk storage this cog is using.

.. _stattrack-command-stattrack-users:

"""""""""""""""
stattrack users
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack users 

**Description**

See stats about user counts

.. _stattrack-command-stattrack-users-bots:

""""""""""""""""""""
stattrack users bots
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack users bots [timespan=1 day, 0:00:00]

**Description**

Get bot user stats.

This is the count of unique bots. They are counted once, regardless of how many servers
they share with me.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack users bots 3w2d``
``[p]stattrack users bots 5d``
``[p]stattrack users bots all``

.. _stattrack-command-stattrack-users-humans:

""""""""""""""""""""""
stattrack users humans
""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack users humans [timespan=1 day, 0:00:00]

**Description**

Get human user stats.

This is the count of unique humans. They are counted once, regardless of how many servers
they share with me.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack users humans 3w2d``
``[p]stattrack users humans 5d``
``[p]stattrack users humans all``

.. _stattrack-command-stattrack-users-total:

"""""""""""""""""""""
stattrack users total
"""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack users total [timespan=1 day, 0:00:00]

**Description**

Get total user stats.

This includes humans and bots and counts users/bots once per server they share with me.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack users total 3w2d``
``[p]stattrack users total 5d``
``[p]stattrack users total all``

.. _stattrack-command-stattrack-users-unique:

""""""""""""""""""""""
stattrack users unique
""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]stattrack users unique [timespan=1 day, 0:00:00]

**Description**

Get total user stats.

This includes humans and bots and counts them once, reagardless of how many servers they
share with me.

**Arguments**

``<timespan>`` How long to look for, or ``all`` for all-time data. Defaults to 1 day. Must be
at least 1 hour.

**Examples:**

``[p]stattrack users unique 3w2d``
``[p]stattrack users unique 5d``
``[p]stattrack users unique all``
