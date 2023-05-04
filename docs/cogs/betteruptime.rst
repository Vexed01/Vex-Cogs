.. _betteruptime:

============
BetterUptime
============

This is the cog guide for the betteruptime cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _betteruptime-usage:

-----
Usage
-----

Replaces the core ``uptime`` command to show the uptime
percentage over the last 30 days.

The cog will need to run for a full 30 days for the full
data to become available.


.. _betteruptime-commands:

--------
Commands
--------

.. _betteruptime-command-downtime:

^^^^^^^^
downtime
^^^^^^^^

**Syntax**

.. code-block:: none

    [p]downtime [num_days=30]

**Description**

Check Red downtime over the last 30 days.

The default value for ``num_days`` is ``30``. You can put ``0`` days for all-time data.
Otherwise, it needs to be ``5`` or more.

**Examples:**
- ``[p]uptime``
- ``[p]uptime 0`` (for all-time data)
- ``[p]uptime 7``

.. _betteruptime-command-resetbu:

^^^^^^^
resetbu
^^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]resetbu 

**Description**

Reset the cog's data.

.. _betteruptime-command-uptime:

^^^^^^
uptime
^^^^^^

**Syntax**

.. code-block:: none

    [p]uptime [num_days=30]

**Description**

Get Red's uptime percent over the last 30 days, and when I was last restarted.

The default value for ``num_days`` is ``30``. You can put ``0`` days for all-time data.
Otherwise, it needs to be ``5`` or more.

.. Note:: embeds must be enabled for this rich data to show


**Examples:**
- ``[p]uptime``
- ``[p]uptime 0`` (for all-time data)
- ``[p]uptime 7``

.. _betteruptime-command-uptimeexport:

^^^^^^^^^^^^
uptimeexport
^^^^^^^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]uptimeexport 

**Description**

Export my uptime data to CSV

The numbers represent uptime, so 86400 means 100% for that day (86400 seconds in 1 day).

Everything is in UTC.

Connected is the bot being connected to Discord.

Cog loaded is the cog being loaded but not necessarily connected to Discord.

Therefore, connected should always be equal to or lower than cog loaded.

.. _betteruptime-command-uptimegraph:

^^^^^^^^^^^
uptimegraph
^^^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]uptimegraph [num_days=30]

**Description**

Check Red uptime with a graph over the last 30 days.

The default value for ``num_days`` is ``30``. You can put ``0`` days for all-time data.
Otherwise, it needs to be ``5`` or more.

**Examples:**
- ``[p]uptime`` - for the default of 30 days
- ``[p]uptime 0`` - for all-time data
-]uptime 7`` - 7 days
