.. _wol:

===
WOL
===

This is the cog guide for the wol cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _wol-usage:

-----
Usage
-----

Send a magic packet (Wake on LAN) to a computer on the local network.

Get started by adding your computer with ``[p]wolset add <friendly_name> <mac>``.
Then you can wake it with ``[p]wol <friendly_name>``.

For example, ``[p]wolset add main_pc 11:22:33:44:55:66`` then you can use
``[p]wol main_pc``


.. _wol-commands:

--------
Commands
--------

.. _wol-command-wol:

^^^
wol
^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]wol <machine>

**Description**

Wake a local computer.

You can set up a short name with ``[p]wolset add`` so you don't need to
write out the MAC each time, or just send the MAC.

**Examples:**
    - ``[p]wol main_pc``
    - ``[p]wol 11:22:33:44:55:66``

.. _wol-command-wolset:

^^^^^^
wolset
^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]wolset 

**Description**

Manage your saved computer/MAC aliases for easy access.

.. _wol-command-wolset-add:

""""""""""
wolset add
""""""""""

**Syntax**

.. code-block:: none

    [p]wolset add <friendly_name> <mac>

**Description**

Add a machine for easy use with ``[p]wol``.

``<friendly_name>`` **cannot** include spaces.

**Examples:**
    - ``wolset add main_pc 11:22:33:44:55:66``
    - ``wolset add main_pc 11-22-33-44-55-66``

.. _wol-command-wolset-list:

"""""""""""
wolset list
"""""""""""

**Syntax**

.. code-block:: none

    [p]wolset list 

**Description**

See your added addresses.

This will send your MAC addresses to current channel.

.. _wol-command-wolset-remove:

"""""""""""""
wolset remove
"""""""""""""

**Syntax**

.. code-block:: none

    [p]wolset remove <friendly_name>

.. tip:: Aliases: ``wolset del``, ``wolset delete``

**Description**

Remove a machine from my list of machines.

**Examples:**
    - ``wolset remove main_pc``
