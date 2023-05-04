.. _fivemstatus:

===========
FiveMStatus
===========

This is the cog guide for the fivemstatus cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _fivemstatus-usage:

-----
Usage
-----

View the live status of a FiveM server, in a updating Discord message.

The message is an embed that updates minutely.


.. _fivemstatus-commands:

--------
Commands
--------

.. _fivemstatus-command-fivemstatus:

^^^^^^^^^^^
fivemstatus
^^^^^^^^^^^

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]fivemstatus 

**Description**

Set up a live FiveM status embed.

To stop updating the message, just delete it.

.. _fivemstatus-command-fivemstatus-maintenance:

"""""""""""""""""""""""
fivemstatus maintenance
"""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]fivemstatus maintenance 

**Description**

Toggle maintenance mode.

.. _fivemstatus-command-fivemstatus-setup:

"""""""""""""""""
fivemstatus setup
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]fivemstatus setup <channel> <server>

**Description**

Set up a FiveM status message.

**Examples:**
- ``[p]fivemstatus setup #status 1.0.1.0:30120``
