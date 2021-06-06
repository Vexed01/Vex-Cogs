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

**Examples:**
    - ``[p]uptime``
    - ``[p]uptime 0`` (for all-time data)
    - ``[p]uptime 7``
