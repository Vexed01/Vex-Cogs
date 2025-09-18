.. _calc:

====
Calc
====

This is the cog guide for the calc cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _calc-usage:

-----
Usage
-----

Calculate simple mathematical expressions.

Use the ``calc`` command to open an interactive calculator using buttons.

You can also enable automatic calculation detection with the ``calcset autocal`` command.
When enabled, the bot will react with ➕ to messages containing valid calculations.


.. _calc-commands:

--------
Commands
--------

.. _calc-command-calc:

^^^^
calc
^^^^

**Syntax**

.. code-block:: none

    [p]calc [expression]

**Description**

Start an interactive calculator using buttons.

If an expression is given, it will be prefilled and calculated.

.. _calc-command-calcset:

^^^^^^^
calcset
^^^^^^^

**Syntax**

.. code-block:: none

    [p]calcset 

**Description**

Calculator settings.

.. _calc-command-calcset-autocal:

"""""""""""""""
calcset autocal
"""""""""""""""

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]calcset autocal [enabled]

**Description**

Toggle automatic calculation detection.

When enabled, the bot will react with ➕ to messages containing valid calculations.
If the message author reacts with ➕ too, the bot will send the calculation result.
