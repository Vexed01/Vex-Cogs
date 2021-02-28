.. _system:

======
System
======

This is the cog guide for the system cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note:: To use this cog, load it by typing this::

        [p]load system

.. _system-usage:

-----
Usage
-----

Get system metrics.

Most commands work on all OSes or omit certian information.
See the help for individual commands for detailed limitations.


.. _system-commands:

--------
Commands
--------

.. _system-command-system:

^^^^^^
system
^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]system 

**Description**

Base command for this cog.

Most commands work on all OSes or omit certian information.
See the help for individual commands for detailed limitations.

.. _system-command-system-all:

""""""""""
system all
""""""""""

**Syntax**

.. code-block:: none

    [p]system all 

**Description**

All the data! Embed only.

.. _system-command-system-cpu:

""""""""""
system cpu
""""""""""

**Syntax**

.. code-block:: none

    [p]system cpu 

**Description**

Get metrics about the CPU.

Platforms: Windows, Linux, Mac OS
.. Note:: CPU frequency is nominal and overall on Windows and Mac OS,

on Linux it's current and per-core.

.. _system-command-system-embedtoggle:

""""""""""""""""""
system embedtoggle
""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]system embedtoggle 

.. tip:: Alias: ``system embed``

**Description**

Toggle embeds on and off for this cog.

Note if embeds are set to False using the ``embedset`` command that will oberride this.

.. _system-command-system-memory:

"""""""""""""
system memory
"""""""""""""

**Syntax**

.. code-block:: none

    [p]system memory 

.. tip:: Alias: ``system mem``

**Description**

Get infomation about memory usage.

Platforms: Windows, Linux, Mac OS

.. _system-command-system-sensors:

""""""""""""""
system sensors
""""""""""""""

**Syntax**

.. code-block:: none

    [p]system sensors [farenheit=False]

.. tip:: Aliases: ``system temp``, ``system temperature``, ``system fan``, ``system fans``

**Description**

Get sensor metrics.

Platforms: Linux

.. _system-command-system-users:

""""""""""""
system users
""""""""""""

**Syntax**

.. code-block:: none

    [p]system users 

**Description**

View logged in users.

Platforms: Windows, Linux, Mac OS

.. note:: PID is not available on Windows, and terminal ususally will show ``Unknown``.

