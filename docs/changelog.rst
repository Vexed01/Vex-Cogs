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
| :ref:`birthday<cl_birthday>`
| :ref:`cmdlog<cl_cmdlog>`
| :ref:`github<cl_github>`
| :ref:`googletrends<cl_googletrends>`
| :ref:`madtranslate<cl_madtranslate>`
| :ref:`stattrack<cl_stattrack>`
| :ref:`status<cl_status>`
| :ref:`system<cl_system>`
| :ref:`timechannel<cl_timechannel>`
| :ref:`uptimeresponder<cl_uptimeresponder>`
| :ref:`wol<cl_wol>`

.. note::
    Changelogs are automaticity generated. As such, there may sometimes be visual glitches
    as I do not check this.


.. _cl_aliases:

=======
Aliases
=======

*********
``1.0.6``
*********

2022-01-15

- Show correct command name

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
``1.1.7``
*********

2021-10-04

- Fix OverflowError in edge cases (ANOTHERPINGCOG-2 on Sentry)

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
``2.1.3``
*********

2022-02-07

- Fix log error in uptime graph

*********
``2.1.2``
*********

2021-11-09

- Fix incorrect percentages in graph annotation

*********
``2.1.1``
*********

2021-11-09

- Limit annotated points on uptime graph to 5

*********
``2.1.0``
*********

2021-11-09

- Move plotting backend to Plotly

*********
``2.0.6``
*********

2021-09-14

- Theoretically fix plotting error in certian situations

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

.. _cl_birthday:

========
Birthday
========

**********
``1.0.10``
**********

2022-02-18

- Fix birthday role logic again

*********
``1.0.9``
*********

2022-02-16

- Fix role perm check

*********
``1.0.8``
*********

2022-02-15

- Add warnings to ``bdset settings`` if channels or roles are incorrectly configured
- Modify internal logic for checking for channel and role perms

*********
``1.0.7``
*********

2022-02-08

- More extensive permission checks

*********
``1.0.6``
*********

2022-02-08

- Ensure announcements are on the correct day when a non-UTC midnight time is used v2

*********
``1.0.5``
*********

2022-02-07

- Ensure announcements are on the correct day when a non-UTC midnight time is used

*********
``1.0.4``
*********

2022-02-06

- Grab the config instance instead of json (#79)

*********
``1.0.3``
*********

2022-02-06

- Catch OverflowError in `bdset zemigrate`

*********
``1.0.2``
*********

2022-02-05

- Add ``[p]bdset zemigrate`` for migrating data from ZeLarp's/flare's fork of Birthdays cog (#77)

*********
``1.0.1``
*********

2022-02-05

- Add ``[p]bdset force`` for admins to force set a user's birthday

*********
``1.0.0``
*********

- Initial release

.. _cl_caseinsensitive:

===============
CaseInsensitive
===============

*********
``1.0.4``
*********

2022-02-18

- Add incompatibility check, at the moment I'm only aware of TickChanger

*********
``1.0.3``
*********

2022-01-30

- Support subcommands (GH #74)
- Support discord.py 2.x
- Support aliases made with the alias cog (GH #75)

*********
``1.0.2``
*********

2021-11-26

- Slightly change behaviour

*********
``1.0.1``
*********

2021-11-26

- Properly name info command

.. _cl_cmdlog:

======
CmdLog
======

*********
``1.4.3``
*********

2021-09-05

- Guard dislash.py with TYPE_CHECKING

*********
``1.4.2``
*********

2021-09-05

- Add support for dislash.py application commands

*********
``1.4.1``
*********

2021-08-28

- Fix AttributeError in sending com log to channel
- Fix AttributeError in handling slash commands from Kowlin's SlashInjector
- Ensure bot has send message permissions when setting log channel
- Fixes CMDLOG-2 and CMDLOG-3 on Sentry

*********
``1.4.0``
*********

2021-08-27

- Add new command (``[p]cmdlog channel``) to log commands to a channel

*********
``1.3.1``
*********

2021-08-24

- Add opt-in telemetry and error reporting

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

.. _cl_covidgraph:

==========
CovidGraph
==========

*********
``1.2.0``
*********

2021-11-28

- Add average line

*********
``1.1.1``
*********

2021-11-28

- Fix multi work counties not being picked up properly

*********
``1.1.0``
*********

2021-11-28

- Support worldwide data, for example ``[p]covidgraph cases world``

*********
``1.0.0``
*********

2021-11-27

- New cog

.. _cl_github:

======
GitHub
======

Note: This cog is scheduled for deprecation in favour of a new cog `ghissues` which
supports buttons, for when they are officially supported in Red

*********
``1.0.1``
*********

2021-08-24

- Add opt-in telemetry and error reporting

.. _cl_googletrends:

============
GoogleTrends
============

*********
``1.1.0``
*********

2022-01-12

- Add a URL button to link to Goole Trends, without any extra libs

*********
``1.0.0``
*********

2021-11-09

- Initial release

.. _cl_madtranslate:

============
MadTranslate
============

*********
``1.0.3``
*********

2022-02-05

- Fix ValueError (#78)

*********
``1.0.2``
*********

2021-08-24

- Add opt-in telemetry and error reporting

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
``1.8.5``
*********

2022-01-30

- Stop using deprecated method ``frame.append``

*********
``1.8.4``
*********

2022-01-26

- Force 2 writes on load instead of 1

*********
``1.8.3``
*********

2022-01-17

- Manually count up unique users to avoid issues with the bot's own cache
- Performance optimisations

*********
``1.8.1``
*********

2022-01-13

- Performance optimisations (from my limited testing with 20k users on a relatively weak Windows machine this yields 4-5X faster loops; only 2X on my Ubuntu VPS)

*********
``1.8.0``
*********

2022-01-08

- Show min, max, average (, and total where applicable) in the graph embeds, #69
- Use Discord's colours in the plots for user statuses, thanks Epic
- Use rolling averages for messages + command plots
- Make the bot type on export commands

*********
``1.7.1``
*********

2021-12-06

- Ensure plot frequency is always 1 or greater, fixing ZeroDivisionError when maxpoints is greater than the actual number of points to plot

*********
``1.7.0``
*********

2021-12-05

- New hidden dev commands: ``stattrack devimport``, ``stattrack debug``
- Significantly improve performance for very large plots (a few months+) by using a maxiumum amount of points to plot, default at 25,000, settable with ``stattrack maxpoints``

*********
``1.6.0``
*********

2021-12-02

- Allow stats in the same group to be shown on a single graph

*********
``1.5.1``
*********

2021-11-28

- Add loop time metric

*********
``1.5.0``
*********

2021-11-28

- Add metrics for CPU and Memory usage percentages

*********
``1.4.0``
*********

2021-11-09

- Move to plotly for the plotting backend

*********
``1.3.2``
*********

2021-09-14

- Fix TypeError in log for when loop overruns

*********
``1.3.1``
*********

2021-08-24

- Add opt-in telemetry and error reporting

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

*********
``2.5.0``
*********

2022-02-07

- Add buttons for discord.py 2.0

*********
``2.4.1``
*********

2021-09-14

- Limit embed value length in status command, for affected components. This did NOT affect the background loop and automatic sending of updates

*********
``2.4.0``
*********

2021-08-26

- Cache status updates, and therefore decrase the cooldown on the `status` command

**********
``2.3.12``
**********

2021-08-24

- Add opt-in telemetry and error reporting

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

**********
``1.3.10``
**********

2022-02-07

- Auto-hide loop disks, old behaviour possible with `[p]system disk False`

*********
``1.3.9``
*********

2021-08-24

- Add opt-in telemetry and error reporting

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
``1.3.1``
*********

2022-01-30

- Show 24 hour time in ``tcset short`` output
- More useful error message when an incorrect identifier is used

*********
``1.3.0``
*********

2022-01-30

- Support 24 hour time by adding ``-24h`` to a short identifier, for example ``[p]tcset create UK: {ni-24h}``

*********
``1.2.2``
*********

2021-08-24

- Add opt-in telemetry and error reporting

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

===============
UptimeResponder
===============

*********
``1.0.0``
*********

2022-02-09

- "New" cog (moved from bounty repo)
- Cog for responding to uptime monitoring service pings.

===
WOL
===

*********
``1.0.5``
*********

2021-08-24

- Add opt-in telemetry and error reporting

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
