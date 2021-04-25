.. _changelog:

=========
Changelog
=========

I may sometimes push an update without incrementing the version. These will not be put in the changelog.

Usage of this for all version bumping updates started 21-04-08.

Date format throughout is YYYY-MM-DD

See the contents bar on the right to skip to a cog.


=======
Aliases
=======

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

==============
AnotherPingCog
==============

*No updates since changelogs started*

========
Beautify
========

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

============
BetterUptime
============

*********
``1.3.0``
*********

- Allow a custom timeframe in ``uptime`` and ``downtime``, eg ``uptime 7``
- Pagify the ``downtime`` command

*********
``1.2.2``
*********

- Slight logic changes for banding in ``downtime`` command

======
CmdLog
======

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

======
GitHub
======

*No updates since changelogs started*

======
Status
======

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

======
System
======

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

=========
Meta Docs
=========

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