.. _timechannel:

===========
TimeChannel
===========

This is the cog guide for the timechannel cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _timechannel-usage:

-----
Usage
-----

Allocate a Discord voice channel to show the time in specific timezones. Updates every hour.

A list of timezones can be found here, though you should be able to enter any
major city: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

There is a fuzzy search so you don't need to put the region in, only the city.

This cog will shrink down from the proper region names, for example ``America/New_York``
will become ``New York``.

The ``[p]timezones`` command (runnable by anyone) will show the full location name.


.. _timechannel-commands:

--------
Commands
--------

.. _timechannel-command-timechannelset:

^^^^^^^^^^^^^^
timechannelset
^^^^^^^^^^^^^^

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]timechannelset 

.. tip:: Alias: ``tcset``

**Description**

Manage channels which will show the time for a timezone.

.. _timechannel-command-timechannelset-create:

"""""""""""""""""""""
timechannelset create
"""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]timechannelset create <timezone>

**Description**

Set up a time channel in this server.

The list of acceptable timezones is here (the "TZ database name" column):
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

There is a fuzzy search, so you shouldn't need to enter the region.

If you move the channel into a category, **click 'Keep Current Permissions' in the sync
permissions dialogue.**

**Examples:**
    - ``[p]tcset create New York``
    - ``[p]tcset create UTC``
    - ``[p]tcset create London``
    - ``[p]tcset create Europe/London``

.. _timechannel-command-timechannelset-remove:

"""""""""""""""""""""
timechannelset remove
"""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]timechannelset remove <channel>

**Description**

Delete and stop updating a channel.

For the <channel> argument, you can use its ID or mention (type #!channelname)

**Example:**
    - ``[p]tcset remove #!channelname`` (the ! is how to mention voice channels)
    - ``[p]tcset remove 834146070094282843``

.. _timechannel-command-timezones:

^^^^^^^^^
timezones
^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]timezones 

**Description**

See the time in all the configured timezones for this server.
