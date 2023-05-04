.. _ghissues:

========
GHIssues
========

This is the cog guide for the ghissues cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _ghissues-usage:

-----
Usage
-----

Create, comment, labelify and close GitHub issues.

This cog is only for bot owners.
I made it for managing issues on my cog repo as a small project,
but it certainly could be used for other situations where you want
to manage GitHub issues from Discord.

If you would like a way to search or view issues, I highly recommend
Kowlin's approved ``githubcards`` cog (on the repo
https://github.com/Kowlin/Sentinel)

At present, this cannot support multiple repos.

PRs are mostly supported. You can comment on them or close them
but not merge them or create them.

Get started with the ``ghi howtoken`` command to set your GitHub token.
You don't have to do this if you have already set it for a different
cog, eg ``githubcards``. Then set up with ``ghi setrepo``.


.. _ghissues-commands:

--------
Commands
--------

.. _ghissues-command-ghi:

^^^
ghi
^^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]ghi <issue>

.. tip:: Alias: ``ghissues``

**Description**

Command to interact with this cog.

All commands are owner only.

To open the interactive issue view, run ``[p]ghi <issue_num>``.

**Examples:**
- ``[p]ghi 11``
- ``[p]ghi howtoken``
- ``[p]ghi newissue``

.. _ghissues-command-ghi-howtoken:

""""""""""""
ghi howtoken
""""""""""""

**Syntax**

.. code-block:: none

    [p]ghi howtoken 

**Description**

Instructions on how to set up a token.

.. _ghissues-command-ghi-newissue:

""""""""""""
ghi newissue
""""""""""""

**Syntax**

.. code-block:: none

    [p]ghi newissue <title>

**Description**

Open a new issue. If you want to reopen, then use the normal interactive view.

.. _ghissues-command-ghi-setrepo:

"""""""""""
ghi setrepo
"""""""""""

**Syntax**

.. code-block:: none

    [p]ghi setrepo <slug>

**Description**

Set up a repo to use as a slug (``USERNAME/REPO``).
