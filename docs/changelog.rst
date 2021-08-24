.. _changelog:

=========
Changelog
=========

I may sometimes push an update without incrementing the version. These will not be put in the changelog.

Usage of this for all version bumping updates started 21-04-08.

Date format throughout is YYYY-MM-DD

Jump links:

| :ref:`aliases<cl_aliases>`
| :ref:`anotherpingcog<cl_apc>`
| :ref:`beautify<cl_beautify>`
| :ref:`betteruptime<cl_betteruptime>`
| :ref:`cmdlog<cl_cmdlog>`
| :ref:`github<cl_github>`
| :ref:`madtranslate<cl_madtranslate>`
| :ref:`stattrack<cl_stattrack>`
| :ref:`status<cl_status>`
| :ref:`system<cl_system>`
| :ref:`timechannel<cl_timechannel>`
| :ref:`wol<cl_wol>`

.. note::
    Changelogs are automaticity generated. As such, there may sometimes be visual glitches
    as I do not check this.


.. _cl_aliases:

=======
Aliases
=======

*********
``1.0.5``
*********

2021-08-24

- Add opt-in telemetry and error reporting

*********
``1.0.4``
*********

2021-04-11

- Fix edge case to hide alias cog aliases if they are a built in command/command alias

*********
``1.0.3``
*********

2021-04-08

- Fix logic for checking command
- Small internal cleanup (still more to do)

.. _cl_apc:

==============
AnotherPingCog
==============

*********
``1.1.6``
*********

2021-08-24

- Add opt-in telemetry and error reporting

*********
``1.1.5``
*********

2021-07-18

- Allow customisation of embed footer (`#35 <https://github.com/Vexed01/Vex-Cogs/pull/35>`_ by `Obi-Wan3 <https://github.com/Obi-Wan3>`_)

*********
``1.1.4``
*********

2021-05-09

- Potentially fix super edge case behaviour with command not registering

.. _cl_beautify:

========
Beautify
========

*********
``1.1.2``
*********

2021-08-24

- Add opt-in telemetry and error reporting

*********
``1.1.1``
*********

2021-04-24

- Internal: switch to ``pyjson5.decode`` instead of ``pyjson5.loads``

*********
``1.1.0``
*********

2021-04-21

-------------------
User-facing changes
-------------------

- Accept more values (True, False and None in that specific casing)

----------------
Internal Changes
----------------

- Cache whether pyjson5 is available instead of catching NameError each time
- Move more stuff to utils to better apply DRY


*********
``1.0.3``
*********

2021-04-21

- Add EUD key to ``__init__.py``

*********
``1.0.2``
*********

2021-04-12

- Remove print statement
- Allow ``py`` codeblocks in replies (eg for beautifying an eval)

*********
``1.0.1``
*********

2021-04-12

- Use JSON5 to support Python dicts

*********
``1.0.0``
*********

2021-04-11

- Initial release

.. _cl_betteruptime:

============
BetterUptime
============

*********
``2.0.5``
*********

2021-08-24

- Add opt-in telemetry and error reporting

*********
``2.0.4``
*********

2021-08-11

- Fix edge case KeyError

*********
``2.0.3``
*********

2021-07-28

- Use Discord's new timestamp format

*********
``2.0.2``
*********

2021-06-21

- Add labels to uptime under 99.7% to graph

*********
``2.0.1``
*********

2021-06-21

- Require 4+ days of data for graph

*********
``2.0.0``
*********

2021-06-21

- Significant internal refactoring to make it more maintainable
- New command: ``uptimegraph`` - see uptime in graph form
- New command: ``uptimeexport`` (bot owner only) - export uptime data to CSV
- Fix removing wrong command on cog unload

*********
``1.6.0``
*********

2021-06-06

- Add `resetbu` command to reset all uptime data

*********
``1.6.0``
*********

2021-05-28

- Fix commands
- Fix config migration

*********
``1.5.2``
*********

2021-05-25

- Remove custom uptime command... There's some broken shit that I can't fix, rewrite was already planned and this will be fixed then (#23 on GitHub)

*********
``1.5.1``
*********

2021-05-23

- Fix deprecation warning

*********
``1.5.0``
*********

2021-05-23

- Move to storing and internally cache data as a Pandas Series

*********
``1.4.1``
*********

2021-05-09

- Fix unreachable code

*********
``1.4.0``
*********

2021-05-01

- Utilise an Abstract Base Class and move to VexLoop

*********
``1.3.0``
*********

2021-04-25

- Allow a custom timeframe in ``uptime`` and ``downtime``, eg ``uptime 7``
- Pagify the ``downtime`` command

*********
``1.2.2``
*********

- Slight logic changes for banding in ``downtime`` command

.. _cl_cmdlog:

======
CmdLog
======

*********
``1.3.0``
*********

2021-08-12

- Support Application Commands (Slash, Message, User), both with slashinjector/dpy 1 and dpy 2

*********
``1.2.1``
*********

2021-08-07

- Initial discord.py 2.0 compatibility

*********
``1.3.0``
*********

2021-06-23

- Add content logging, by deafult turned off (see command ``[p]cmdlog content``)
- Simplify EUD statement
- Add info on how long long since cog load (how long current cache lasts) on log commands

*********
``1.1.0``
*********

2021-05-10

- Log command invoke message IDs
- Round cache size to 1 decimal place

*********
``1.0.2``
*********

2021-04-22

- Return correct size... I really thought I already did this.

*********
``1.0.1``
*********

2021-04-18

- New command to view cache size (``cmdlog cache``)

*********
``1.0.0``
*********

2021-04-18

- Initial release

.. _cl_github:

======
GitHub
======

*No updates since changelogs started*

Note: This cog is scheduled for deprecation in favour of a new cog `ghissues` which
supports buttons, for when they are officially supported in Red

.. _cl_madtranslate:

============
MadTranslate
============

*********
``1.0.1``
*********

2021-06-07

- Add Vex-Cog-Utils stuff

*********
``1.0.0``
*********

2021-06-07

- Initial release

.. _cl_stattrack:

=========
StatTrack
=========

*********
``1.3.0``
*********

2021-08-11

- Move to SQLite driver in Vex-Cog-Utils

*********
``1.1.0``
*********

2021-06-25

- Move to SQLite for data storage for superior speed

*********
``1.0.1``
*********

2021-06-12

- Count time to save to config seperatleu

*********
``1.0.0``
*********

2021-06-02

- Initial release

.. _cl_status:

======
Status
======

**********
``2.3.11``
**********

2021-08-16

- Change service base image URL to static.vexcodes.com

**********
``2.3.10``
**********

2021-08-07

- Initial discord.py 2.0 compatibility

*********
``2.3.9``
*********

2021-06-27

- Improve embed limit handling

*********
``2.3.8``
*********

2021-06-22

- Move icons to GH Pages
- Make field name a zero width space for when embed fields are split

*********
``2.3.7``
*********

2021-06-17

- Fix edge case KeyError with service restrictions

*********
``2.3.6``
*********

2021-06-08

- New service - Fastly
- Handle embed description limits

*********
``2.3.5``
*********

2021-05-22

- Update to use Discord's new logo

*********
``2.3.4``
*********

2021-05-19

- Fix KeyError which could occur in edge cases

*********
``2.3.3``
*********

2021-05-16

- Change the colour for ``investigating`` to orange (from red)

*********
``2.3.2``
*********

2021-05-08

- Dynamic help for avalible services in all commands that previously had them listed

*********
``2.3.0``
*********

2021-05-05

- Use dedicated library (``markdownify``) for handling HTML to markdown
- Remove ``pytz`` for requirements and remove from code.

*********
``2.2.0``
*********

2021-05-01

- Use the ABC in the loop and move to VexLoop

*********
``2.1.5``
*********

2021-05-01

- Properly handle errors relating to service restrictions when removing a feed
- Improve error handling/logging in update loop
- Limit number of updates sent per service per check to 3 (eg when cog has been unloaded for a while)

*********
``2.1.4``
*********

2021-04-23

- Show status of components in command ``status``

*********
``2.1.3``
*********

2021-04-22

- Use deque for cooldown

*********
``2.1.2``
*********

- Handle EUD data deletion requests (return None)

*********
``2.1.1``
*********

2021-13-04

- Minor refactoring

*********
``2.1.0``
*********

2021-13-04

-------------------
User-facing changes
-------------------

- Handle HTML tags for Oracle Cloud

----------------
Internal changes
----------------

- Utilise an Abstract Base Class
- Add some internal docstrings

********************
``2.0.0``, ``2.0.1``
********************

(backdated)

---------
Important
---------

**If the cog fails to load after updating** then you'll need to do the following.

.. note::
    If you originally added my repo and didn't name it ``vex``,  replace ``vex`` with what you called it throughout.

1. Uninstall status and remove my repo
    .. code-block:: none

        cog uninstall status

    .. code-block:: none

        repo remove vex

2. Add my repo back and reinstall status
    .. code-block:: none

        repo add vex https://github.com/Vexed01/Vex-Cogs

    .. code-block::

        cog install vex status

3. Restart
    .. code-block:: none

        restart

    .. note::
        If you haven't configured anything to catch the restart, you'll need to start your bot up again.

    You should now be able to load the cog.

-------------------
User-facing changes
-------------------

- BREAKING CHANGES: Removed AWS, GCP, Twitter and Status.io. These will be automaticity removed when you update.
- Added the docs page :ref:`statusref` to see previews for different modes/webhook
- All updates will now included the impact and affected components (see an example at :ref:`statusref`)
- New service: GeForce NOW (``geforcenow``)

----------------------------
Event Changes for developers
----------------------------

I highly recommend you read the docs page again at the :ref:`statusdev` page.

There have been significant changes to both the events.

----------------
Internal changes
----------------

- Significant re-factoring into more files and folders
- Rewrite of update checking and sending logic
- Implementation of Status API instead of parsing RSS
- Changes to how incidents are stored including config wrapper
- No longer write ETags to config (just cache)

.. _cl_system:

======
System
======

*********
``1.3.8``
*********

2021-08-11

- Use correct timezone for system uptime

*********
``1.3.7``
*********

2021-08-09

- Fix error on d.py 2

*********
``1.3.6``
*********

2021-08-07

- Initial discord.py 2.0 compatibility

*********
``1.3.5``
*********

2021-06-30

- Change formatting of ``system red`` and it's corresponding section of ``system all``

*********
``1.3.4``
*********

2021-06-29

- Fix ``system all`` non-embed output

*********
``1.3.5``
*********

2021-06-27

- Show Red's resource usage in the ``system all`` command
- Trigger typing for ``system red`` command
- Use the bot's name for Red's resource usage instead of just "Red"

*********
``1.3.2``
*********

2021-06-25

- Correctly display SWAP usage

*********
``1.3.1``
*********

2021-06-25

- New command: ``[p]system red``

*********
``1.2.7``
*********

2021-06-18

- Make the cog compatible with WSL

*********
``1.2.6``
*********

2021-06-18

- Use UTC for bot uptime

*********
``1.2.5``
*********

2021-06-18

- Handle no CPU frequency data being avalible

*********
``1.2.4``
*********

2021-06-13

- Fix formatting of cpu

*********
``1.2.3``
*********

2021-06-12

- Add bot uptime to footer

*********
``1.2.2``
*********

2021-06-12

- Show uptime in footer for all commands
- Make embed formatting to two columns dynamic

*********
``1.2.1``
*********

2021-05-30

- Handle embed limits

*********
``1.2.0``
*********

2021-05-30

- Add command ``system net``
- Use AsyncIter for the process generator

*********
``1.1.2``
*********

2021-05-08

- Dynamic help showing if commands are avablible on your system

*********
``1.1.1``
*********

2021-04-09

- Add missing docstring for ``system uptime``
- (internal) Add stubs for psutil

*********
``1.1.0``
*********

2021-04-08

- New command: ``system uptime``
    - shows what time the system was booted and how long ago that was
- Internal refactor, splitting commands and psutil parsers into two files

.. _cl_timechannel:

===========
TimeChannel
===========

*********
``1.2.1``
*********

2021-08-07

- Initial discord.py 2.0 compatibility

*********
``1.2.0``
*********

2021-06-25

- You can now choose your own format. Take a look at ``[p]tcset create`` for some infomation on how to do so. You'll have to remove old channels with ``[p]tcset remove``

*********
``1.1.1``
*********

2021-06-07

- Fix inconsistencies

*********
``1.1.0``
*********

2021-05-02

- Improve fuzzy timezone search

*********
``1.0.0``
*********

2021-05-01

- Initial release

.. _cl_wol:

===
WOL
===

*********
``1.0.4``
*********

2021-08-20

- More realease testing...

*********
``1.0.3``
*********

2021-08-20

- Stil testing release workflow...

*********
``1.0.2``
*********

2021-08-20

- Still testing release workflow...

*********
``1.0.1``
*********

2021-08-20

- Testing release workflow, please ignore

*********
``1.0.0``
*********

2021-05-31

- Initial release

.. _cl_docs:

=========
Meta Docs
=========

*********
``2.2.0``
*********

2021-06-21

- Directly link to each section at the top of changelog

*********
``2.1.1``
*********

2021-04-11

- Change intro at top to link to :ref:`getting_started` instead of saying to load the cog
- Bring docs up to date with docstring in all cogs

*********
``2.1.0``
*********

2021-04-08

- Start versioning docs
- Fully use changelog

*********
``2.0.0``
*********

(backdated)

- Switch to furo theme
