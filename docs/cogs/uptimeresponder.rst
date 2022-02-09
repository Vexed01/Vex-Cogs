.. _uptimeresponder:

===============
UptimeResponder
===============

This is the cog guide for the uptimeresponder cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _uptimeresponder-usage:

-----
Usage
-----

A cog for responding to pings form various uptime monitoring services,
such as UptimeRobot, Pingdom, Uptime.com, or self-hosted ones like UptimeKuma or Upptime.

The web server will run in the background whenever the cog is loaded on the specified port.


.. _uptimeresponder-commands:

--------
Commands
--------

.. _uptimeresponder-command-uptimeresponderport:

^^^^^^^^^^^^^^^^^^^
uptimeresponderport
^^^^^^^^^^^^^^^^^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]uptimeresponderport [port]

**Description**

Get or set the port to run the simple web server on.

Run the command on it's own (``[p]uptimeresponderport``) to see what it's set to at the moment,
and to set it run ``[p]uptimeresponderport 8080``, for example.
