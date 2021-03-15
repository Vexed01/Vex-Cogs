.. _github:

======
GitHub
======

This is the cog guide for the github cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note:: To use this cog, load it by typing this::

        [p]load github

.. _github-usage:

-----
Usage
-----

Create, comment, labelify and close GitHub issues.

This cog is only for bot owners.
I made it for managing issues on my cog repo as a small project,
but it certainly could be used for other situations where you want
to manage GitHub issues from Discord.

If you would like a way to search or view issues, I highly reccomend
Kowlin's approved ``githubcards`` cog (on the repo
https://github.com/Kowlin/Sentinel)

At present, this cannot support multiple repos.

PRs are mostly supported. You can comment on them or close them
but not merge them or create them.

Get started with the ``gh howtoken`` command to set your GitHub token.
You don't have to do this if you have already set it for a different
cog, eg ``ghcards``. Then set up with ``gh setrepo``.


.. _github-commands:

--------
Commands
--------

.. _github-command-gh:

^^
gh
^^

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]gh 

.. tip:: Alias: ``github``

**Description**

Base command for interacting with this cog.

All commands are owner only.

.. _github-command-gh-addlabels:

""""""""""""
gh addlabels
""""""""""""

**Syntax**

.. code-block:: none

    [p]gh addlabels <issue>

.. tip:: Alias: ``gh addlabel``

**Description**

Interactive command to add labels to an issue or PR.

.. _github-command-gh-close:

""""""""
gh close
""""""""

**Syntax**

.. code-block:: none

    [p]gh close <issue>

**Description**

Close an issue or PR.

.. _github-command-gh-comment:

""""""""""
gh comment
""""""""""

**Syntax**

.. code-block:: none

    [p]gh comment <issue> <text>

**Description**

Comment on an issue or PR.

.. _github-command-gh-commentclose:

"""""""""""""""
gh commentclose
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]gh commentclose <issue> <text>

**Description**

Comment on, then close, an issue or PR.

.. _github-command-gh-howtoken:

"""""""""""
gh howtoken
"""""""""""

**Syntax**

.. code-block:: none

    [p]gh howtoken 

**Description**

Instructions on how to set up a token.

.. _github-command-gh-open:

"""""""
gh open
"""""""

**Syntax**

.. code-block:: none

    [p]gh open <title>

**Description**

Open a new issue. Does NOT reopen.

.. _github-command-gh-removelabels:

"""""""""""""""
gh removelabels
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]gh removelabels <issue>

.. tip:: Alias: ``gh removelabel``

**Description**

Interactive command to remove labels from an issue or PR.

.. _github-command-gh-setrepo:

""""""""""
gh setrepo
""""""""""

**Syntax**

.. code-block:: none

    [p]gh setrepo <slug>

**Description**

Set up a repo to use as a slug (``USERNAME/REPO``).
