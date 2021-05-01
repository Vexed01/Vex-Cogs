.. _getting_started:

===============
Getting my cogs
===============

``[p]`` is your prefix.

.. note::
    You can replace ``vex`` with whatever you want, but you'll need to type it
    out every time you install one of my cogs so make sure it's simple. Note
    it's case sensitive.

1. First, you need to add the my repository (repo):
    .. code-block:: none

        [p]repo add vex-cogs https://github.com/Vexed01/Vex-Cogs

2. Now you can install my cogs with this command:
    .. code-block:: none

        [p]cog install vex-cogs cogname

3. Finally, you need to load the cog:
    .. code-block:: none

        [p]load cogname


You can list my cogs with this command:

.. code-block:: none

    [p]cog list vex-cogs

.. tip::

    It's a good idea to keep cogs up to date. You should run this command
    every now and again to update all your cogs:

    .. code-block:: none

        [p]cog update

----
Cogs
----

Click a cog name to see detailed documentation.

===================================== ===========================================================================
Cog name                              Summary
===================================== ===========================================================================
:ref:`aliases<aliases>`               Get all the information you could ever need about a command's aliases.
:ref:`anotherpingcog<anotherpingcog>` Just another ping cog... But this one has fancy colours in an embed!
:ref:`beautify<beautify>`             Beautify and minify JSON.
:ref:`betteruptime<betteruptime>`     New uptime command that tracks the bot's uptime percentage (last 30 days).
:ref:`cmdlog<cmdlog>`                 Track command usage, searchable by user, server or command name.
:ref:`github<github>`                 Create, comment, labelify and close GitHub issues, with partial PR support.
:ref:`status<status>`                 Recieve automatic status updates from various services, including Discord.
:ref:`system<system>`                 Get system metrics of the host device, such as RAM or CPU.
:ref:`timechannel<timechannel>`       Get the time in different timezones in voice channels.
===================================== ===========================================================================