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

    [p]timechannelset create <string>

**Description**

Set up a time channel in this server.

If you move the channel into a category, **click 'Keep Current Permissions' in the sync
permissions dialogue.**

**How to use this command:**

First, use the ``[p]tcset short <long_tz>`` to get the short identifier for the
timezone of your choice.

Once you've got a short identifier from ``tcset short``, you can use it in this command.
Simply put curly brackets, ``{`` and ``}`` around it, and it will be replaced with the time.

**For example**, running ``[p]tcset short new york`` gives a short identifier of ``fv``.
This can then be used like so:
``[p]tcset create 🕑️ New York: {fv}``.

You could also use two in one, for example
``[p]tcset create UK: {ni} FR: {nr}``

The default is 12 hour time, but you can use ``{shortid-24h}`` for 24 hour time,
eg ``{ni-24h}``

**More Examples:**
    - ``[p]tcset create 🕑️ New York: {fv}``
    - ``[p]tcset create 🌐 UTC: {qw}``
    - ``[p]tcset create {ni-24h} in London``
    - ``[p]tcset create US Pacific: {qv-24h}``

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

.. _timechannel-command-timechannelset-short:

""""""""""""""""""""
timechannelset short
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]timechannelset short <timezone>

**Description**

Get the short identifier for the main ``create`` command.

The list of acceptable timezones is here (the "TZ database name" column):
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

There is a fuzzy search, so you shouldn't need to enter the region.

Please look at ``[p]help tcset create`` for more information.

**Examples:**
    - ``[p]tcset short New York``
    - ``[p]tcset short UTC``
    - ``[p]tcset short London``
    - ``[p]tcset short Europe/London``

.. _timechannel-command-timezones:

^^^^^^^^^
timezones
^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]timezones 

**Description**

See the time in all the configured timezones for this server.
