.. _autoping:

========
AutoPing
========

This is the cog guide for the autoping cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _autoping-usage:

-----
Usage
-----

Automatically ping a user/role when a message is sent in a channel.

Can be used to notify a user or role when a message is sent in a channel.

Pings are always sent in the channel the message was sent in.

Pings are rate limited to a default of 1 per hour.

If the latest message in the channel when a ping is about to be sent includes a ping of the target user OR is sent by the target user, that user will not be pinged. Roles are always pinged.

Messages from bots/webhooks are ignored.

Anyone can run ``autoping add`` to add themselves to the autoping list for the channel, and users with manage messages permissions or mod can add other users/roles. You can restrict this with the Permissions cog.

Only users with manage message permissions or mod can change the rate limit.


.. _autoping-commands:

--------
Commands
--------

.. _autoping-command-autoping:

^^^^^^^^
autoping
^^^^^^^^

**Syntax**

.. code-block:: none

    [p]autoping 

**Description**

Configure autopings for this channel.

.. _autoping-command-autoping-add:

""""""""""""
autoping add
""""""""""""

**Syntax**

.. code-block:: none

    [p]autoping add [target]

**Description**

Add yourself or a user/role to the autoping list for this channel.

Only moderators can add other users or roles.

**Examples:**
- ``[p]autoping add`` to add yourself to the list.
- ``[p]autoping add @user`` to add a user to the list.
- ``[p]autoping add ID`` to add a role/user by ID.
- ``[p]autoping add Role Name`` to add a role by name.

.. _autoping-command-autoping-clear:

""""""""""""""
autoping clear
""""""""""""""

.. note:: |mod-lock|

**Syntax**

.. code-block:: none

    [p]autoping clear 

**Description**

Clear the autoping list for this channel.

Only moderators can clear the list.

.. _autoping-command-autoping-ratelimit:

""""""""""""""""""
autoping ratelimit
""""""""""""""""""

.. note:: |mod-lock|

**Syntax**

.. code-block:: none

    [p]autoping ratelimit <time>

**Description**

Set the rate limit for autoping in this channel.

Only moderators can change the rate limit.

**Examples:**
- ``[p]autoping ratelimit 10 minutes`` to set the rate limit to 10 minutes.
- ``[p]autoping ratelimit 1 hour`` to set the rate limit to 1 hour.

.. _autoping-command-autoping-remove:

"""""""""""""""
autoping remove
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]autoping remove [target]

**Description**

Remove yourself or a user/role from the autoping list for this channel.

Only moderators can remove other users or roles.

**Examples:**
- ``[p]autoping remove`` to remove yourself from the list.
- ``[p]autoping remove @user`` to remove a user from the list.
- ``[p]autoping remove ID`` to remove a role/user by ID.
- ``[p]autoping remove Role Name`` to remove a role by name.

.. _autoping-command-autoping-settings:

"""""""""""""""""
autoping settings
"""""""""""""""""

.. note:: |mod-lock|

**Syntax**

.. code-block:: none

    [p]autoping settings 

**Description**

Show the current autoping settings for this channel.

Only moderators can view the settings.

Also shows currently added users and roles.
