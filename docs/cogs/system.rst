.. _system:

======
System
======

This is the cog guide for the system cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

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

Get information about your system metrics.

Most commands work on all OSes or omit certian information.
See the help for individual commands for detailed limitations.

.. _system-command-system-all:

""""""""""
system all
""""""""""

**Syntax**

.. code-block:: none

    [p]system all 

.. tip:: Aliases: ``system overview``, ``system top``

**Description**

Get an overview of the current system metrics, similar to ``top``.

This will show CPU utilisation, RAM usage and uptime as well as
active processes.

Platforms: Windows, Linux, Mac OS


.. note:: This command appears to be very slow in Windows.



.. _system-command-system-cpu:

""""""""""
system cpu
""""""""""

**Syntax**

.. code-block:: none

    [p]system cpu 

**Description**

Get metrics about the CPU.

This will show the CPU usage as a percent for each core, and frequency depending on
platform.
It will also show the time spent idle, user and system as well as uptime.

Platforms: Windows, Linux, Mac OS


.. note::
    CPU frequency is nominal and overall on Windows and Mac OS,
    on Linux it's current and per-core.

.. _system-command-system-disk:

"""""""""""
system disk
"""""""""""

**Syntax**

.. code-block:: none

    [p]system disk [ignore_loop=True]

.. tip:: Alias: ``system df``

**Description**

Get infomation about disks connected to the system.

This will show the space used, total space, filesystem and
mount point (if you're on Linux make sure it's not potentially
sensitive if running the command a public space).

If ``ignore_loop`` is set to ``True``, this will ignore any loop (fake) devices on Linux.

Platforms: Windows, Linux, Mac OS
.. note::
    Mount point is basically useless on Windows as it's the
    same as the drive name, though it's still shown.

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

.. _system-command-system-network:

""""""""""""""
system network
""""""""""""""

**Syntax**

.. code-block:: none

    [p]system network 

.. tip:: Alias: ``system net``

**Description**

Get network stats. They may have overflowed and reset at some point.

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

.. _system-command-system-red:

""""""""""
system red
""""""""""

**Syntax**

.. code-block:: none

    [p]system red 

**Description**

See what resources Red is using.

Platforms: Windows, Linux, Mac OS


.. note:: SWAP memory information is only available on Linux.


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

.. _system-command-system-uptime:

"""""""""""""
system uptime
"""""""""""""

**Syntax**

.. code-block:: none

    [p]system uptime 

.. tip:: Alias: ``system up``

**Description**

Get the system boot time and how long ago it was.

Platforms: Windows, Linux, Mac OS

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
