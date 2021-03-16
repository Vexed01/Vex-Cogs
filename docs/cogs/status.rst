.. _status:

======
Status
======

This is the cog guide for the status cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note:: To use this cog, load it by typing this::

        [p]load status

.. _status-usage:

-----
Usage
-----

Automatically check for status updates.

When there is one, it will send the update to all channels that
have registered to recieve updates from that service.

If there's a service that you want added, contact Vexed#3211 or
make an issue on the GitHub repo (or even better a PR!).


.. _status-commands:

--------
Commands
--------

.. _status-command-statusset:

^^^^^^^^^
statusset
^^^^^^^^^

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]statusset 

**Description**

Base command for managing the Status cog.

.. _status-command-statusset-add:

"""""""""""""
statusset add
"""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset add <service> [channel]

**Description**

Start getting status updates for the chosen service!

There is a list of services you can use in the ``[p]statusset list`` command.

You can use the ``[p]statusset preview`` command to see how different options look.

If you don't specify a specific channel, I will use the current channel.

This is an interactive command.

.. _status-command-statusset-edit:

""""""""""""""
statusset edit
""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit 

**Description**

Base command for editing services

.. _status-command-statusset-edit-mode:

"""""""""""""""""""
statusset edit mode
"""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit mode <service> [channel] <mode>

**Description**

Change what mode to use for updates

**All**: Every time the service posts an update on an incident, I will send a new message
containing the previous updates as well as the new update. Best used in a fast-moving
channel with other users.

**Latest**: Every time the service posts an update on an incident, I will send a new message
containing only the latest update. Best used in a dedicated status channel.

**Edit**: When a new incident is created, I will sent a new message. When this incident is
updated, I will then add the update to the original message. Best used in a dedicated
status channel.

If you don't specify a channel, I will use the current channel.

.. _status-command-statusset-edit-webhook:

""""""""""""""""""""""
statusset edit webhook
""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit webhook <service> [channel] <webhook>

**Description**

Set whether or not to use webhooks to send the status update

Using a webhook means that the status updates will be sent with the avatar as the service's
logo and the name will be ``[service] Status Update``, instead of my avatar and name.

If you don't specify a channel, I will use the current channel.

.. _status-command-statusset-list:

""""""""""""""
statusset list
""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset list [service]

.. tip:: Aliases: ``statusset show``, ``statusset settings``

**Description**

List that available services and which ones are being used in this server.

Optionally add a service at the end of the command to view detailed settings for that service.

.. _status-command-statusset-preview:

"""""""""""""""""
statusset preview
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset preview <service> <mode> <webhook>

**Description**

Preview what status updates will look like

**Service**

The service you want to preview. There's a list of available services in the
``[p]statusset list`` command.

**<mode>**

    **All**: Every time the service posts an update on an incident, I will send
    a new message containing the previous updates as well as the new update. Best
    used in a fast-moving channel with other users.

    **Latest**: Every time the service posts an update on an incident, I will send
    a new message containing only the latest update. Best used in a dedicated status
    channel.

    **Edit**: Naturally, edit mode can't have a preview so won't work with this command.
    The message content is the same as the ``all`` mode.
    When a new incident is created, I will sent a new message. When this
    incident is updated, I will then add the update to the original message. Best
    used in a dedicated status channel.


**<webhook>**

    Using a webhook means that the status updates will be sent with the avatar
    as the service's logo and the name will be ``[service] Status Update``, instead
    of my avatar and name.

.. _status-command-statusset-remove:

""""""""""""""""
statusset remove
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset remove <service> [channel]

.. tip:: Aliases: ``statusset del``, ``statusset delete``

**Description**

Stop status updates for a specific service in this server.

If you don't specify a channel, I will use the current channel.
