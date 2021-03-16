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

Most commands work on all OSes or omit certain information.
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

.. _system-command-system-cpu:

""""""""""
system cpu
""""""""""

**Syntax**

.. code-block:: none

    [p]system cpu 

**Description**

Get metrics about the CPU.

This will show the CPU usage as a percent for each core, and frequency depending on platform.
It will also show the time spent idle, user and system as well as uptime.

Platforms: Windows, Linux, Mac OS
.. Note:: CPU frequency is nominal and overall on Windows and Mac OS,

on Linux it's current and per-core.

.. _system-command-system-disk:

"""""""""""
system disk
"""""""""""

**Syntax**

.. code-block:: none

    [p]system disk 

.. tip:: Alias: ``system df``

**Description**

Get infomation about disks connected to the system.

This will show the space used, total space, filesystem and
mount point (if you're on Linux make sure it's not potentially
sensitive if running the command a public space).

Platforms: Windows, Linux, Mac OS

.. note::
    Mount point is basically useless on Windows as it's the
    same as the drive name, though it's still shown.

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

.. note:: If embeds are set to False using the ``embedset`` command that will override this.


.. _system-command-system-mem:

""""""""""
system mem
""""""""""

**Syntax**

.. code-block:: none

    [p]system mem 

.. tip:: Aliases: ``system memory``, ``system ram``

**Description**

Get infomation about memory usage.

This will show memory available as a percent, memory used and available as well
as the total amount. Data is provided for both physical and SWAP RAM.

Platforms: Windows, Linux, Mac OS

.. _system-command-system-processes:

""""""""""""""""
system processes
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]system processes 

.. tip:: Alias: ``system proc``

**Description**

Get an overview of the status of currently running processes.

Platforms: Windows, Linux, Mac OS

.. _system-command-system-sensors:

""""""""""""""
system sensors
""""""""""""""

**Syntax**

.. code-block:: none

    [p]system sensors [fahrenheit=False]

.. tip:: Aliases: ``system temp``, ``system temperature``, ``system fan``, ``system fans``

**Description**

Get sensor metrics.

This will return any data about temperature and fan sensors it can find.
If there is no name for an individual sensor, it will use the name of the
group instead.

Platforms: Linux

.. _system-command-system-top:

""""""""""
system top
""""""""""

**Syntax**

.. code-block:: none

    [p]system top 

.. tip:: Aliases: ``system overview``, ``system all``

**Description**

Get an overview of the current system metrics, similar to ``top``.

This will show CPU utilisation, RAM usage and uptime as well as
active processes.

Platforms: Windows, Linux, Mac OS

.. note:: This command appears to be very slow in Windows.


.. _system-command-system-users:

""""""""""""
system users
""""""""""""

**Syntax**

.. code-block:: none

    [p]system users 

**Description**

Get information about logged in users.

This will show the user name, what terminal they're logged in at,
and when they logged in.

Platforms: Windows, Linux, Mac OS

.. note:: PID is not available on Windows. Terminal is usually ``Unknown``

