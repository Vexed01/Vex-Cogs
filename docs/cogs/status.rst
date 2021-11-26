.. _status:

======
Status
======

This is the cog guide for the status cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _status-usage:

-----
Usage
-----

Automatically check for status updates.

When there is one, it will send the update to all channels that
have registered to recieve updates from that service.

There's also the ``status`` command which anyone can use to check
updates whereever they want.

If there's a service that you want added, contact Vexed#9000 or
make an issue on the GitHub repo (or even better a PR!).


.. _status-commands:

--------
Commands
--------

.. _status-command-status:

^^^^^^
status
^^^^^^

**Syntax**

.. code-block:: none

    [p]status <service>

**Description**

Check for the status of a variety of services, eg Discord.

**Example:**
    - ``[p]status discord``

.. _status-command-statusset:

^^^^^^^^^
statusset
^^^^^^^^^

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]statusset

**Description**

Get automatic status updates in a channel, eg Discord.

Get started with ``[p]statusset preview`` to see what they look like,
then ``[p]statusset add`` to set up automatic updates.

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

This is an interactive command. It will ask what mode you want to use and if you
want to use a webhook. You can use the ``[p]statusset preview`` command to see how
different options look or take a look at
https://s.vexcodes.com/c/statusref

If you don't specify a specific channel, I will use the current channel.

.. _status-command-statusset-edit:

""""""""""""""
statusset edit
""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit

**Description**

Edit services you've already set up.

.. _status-command-statusset-edit-mode:

"""""""""""""""""""
statusset edit mode
"""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit mode [channel] <service> <mode>

**Description**

Change what mode to use for status updates.

**All**: Every time the service posts an update on an incident, I will send a new message
containing the previous updates as well as the new update. Best used in a fast-moving
channel with other users.

**Latest**: Every time the service posts an update on an incident, I will send a new
message containing only the latest update. Best used in a dedicated status channel.

**Edit**: When a new incident is created, I will sent a new message. When this incident is
updated, I will then add the update to the original message. Best used in a dedicated
status channel.

If you don't specify a channel, I will use the current channel.

**Examples:**
    - ``[p]statusset edit mode #testing discord latest``
    - ``[p]statusset edit mode discord edit`` (for current channel)

.. _status-command-statusset-edit-restrict:

"""""""""""""""""""""""
statusset edit restrict
"""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit restrict [channel] <service> <restrict>

**Description**

Restrict access to the service in the ``status`` command.

Enabling this will reduce spam. Instead of sending the whole update
(if there's an incident) members will instead be redirected to channels
that automatically receive the status updates, that they have permission to to view.

**Examples:**
    - ``[p]statusset edit restrict #testing discord true``
    - ``[p]statusset edit restrict discord false`` (for current channel)

.. _status-command-statusset-edit-webhook:

""""""""""""""""""""""
statusset edit webhook
""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset edit webhook [channel] <service> <webhook>

**Description**

Set whether or not to use webhooks for status updates.

Using a webhook means that the status updates will be sent with the avatar as the service's
logo and the name will be ``[service] Status Update``, instead of my avatar and name.

If you don't specify a channel, I will use the current channel.

**Examples:**
    - ``[p]statusset edit webhook #testing discord true``
    - ``[p]statusset edit webhook discord false`` (for current channel)

.. _status-command-statusset-list:

""""""""""""""
statusset list
""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset list [service]

.. tip:: Aliases: ``statusset show``, ``statusset settings``

**Description**

List that available services and ones are used in this server.

Optionally add a service at the end of the command to view detailed settings for that
service.

**Examples:**
    - ``[p]statusset list discord``
    - ``[p]statusset list``

.. _status-command-statusset-preview:

"""""""""""""""""
statusset preview
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]statusset preview <service> <mode> <webhook>

**Description**

Preview what status updates will look like.

You can also see this at https://s.vexcodes.com/c/statusref

**<service>**

    The service you want to preview. There's a list of available services in the
    ``[p]help statusset`` command.

**<mode>**

    **all**: Every time the service posts an update on an incident, I will send
    a new message containing the previous updates as well as the new update. Best
    used in a fast-moving channel with other users.

    **latest**: Every time the service posts an update on an incident, I will send
    a new message containing only the latest update. Best used in a dedicated status
    channel.

    **edit**: Naturally, edit mode can't have a preview so won't work with this command.
    The message content is the same as the ``all`` mode.
    When a new incident is created, I will sent a new message. When this
    incident is updated, I will then add the update to the original message. Best
    used in a dedicated status channel.

**<webhook>**

    Using a webhook means that the status updates will be sent with the avatar
    as the service's logo and the name will be ``[service] Status Update``, instead
    of my avatar and name.

**Examples:**
    - ``[p]statusset preview discord all true``
    - ``[p]statusset preview discord latest false``

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

**Examples:**
    - ``[p]statusset remove discord #testing``
    - ``[p]statusset remove discord`` (for using current channel)
