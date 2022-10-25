.. _birthday:

========
Birthday
========

This is the cog guide for the birthday cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _birthday-usage:

-----
Usage
-----

Birthdays

Set yours and get a message and role on your birthday!


.. _birthday-commands:

--------
Commands
--------

.. _birthday-command-bdset:

^^^^^
bdset
^^^^^

.. note:: |admin-lock|

**Syntax**

.. code-block:: none

    [p]bdset 

**Description**

Birthday management commands for admins.

Looking to set your own birthday? Use ``[p]birthday set`` or ``[p]bday set``.

.. _birthday-command-bdset-channel:

"""""""""""""
bdset channel
"""""""""""""

**Syntax**

.. code-block:: none

    [p]bdset channel <channel>

**Description**

Set the channel where the birthday message will be sent.

**Example:**
    - ``[p]bdset channel #birthdays`` - set the channel to #birthdays

.. _birthday-command-bdset-force:

"""""""""""
bdset force
"""""""""""

**Syntax**

.. code-block:: none

    [p]bdset force <user> <birthday>

**Description**

Force-set a specific user's birthday.

You can @ mention any user or type out their exact name. If you're typing out a name with
spaces, make sure to put quotes around it (``"``).

**Examples:**
    - ``[p]bdset set @User 1-1-2000`` - set the birthday of ``@User`` to 1/1/2000
    - ``[p]bdset set User 1/1`` - set the birthday of ``@User`` to 1/1/2000
    - ``[p]bdset set "User with spaces" 1-1`` - set the birthday of ``@User with spaces``
    to 1/1
    - ``[p]bdset set 354125157387344896 1/1/2000`` - set the birthday of ``@User`` to 1/1/2000

.. _birthday-command-bdset-interactive:

"""""""""""""""""
bdset interactive
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]bdset interactive 

**Description**

Start interactive setup

.. _birthday-command-bdset-msgwithoutyear:

""""""""""""""""""""
bdset msgwithoutyear
""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]bdset msgwithoutyear <message>

**Description**

Set the message to be send when the user did not provide a year.

If you would like to mention a role, you will need to run ``[p]bdset rolemention true``.

**Placeholders:**
    - ``{name}`` - the user's name
    - ``{mention}`` - an @ mention of the user

    All the placeholders are optional.

**Examples:**
    - ``[p]bdset msgwithoutyear Happy birthday {mention}!``
    - ``[p]bdset msgwithoutyear {mention}'s birthday is today! Happy birthday {name}.``

.. _birthday-command-bdset-msgwithyear:

"""""""""""""""""
bdset msgwithyear
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]bdset msgwithyear <message>

**Description**

Set the message to be send when the user did provide a year.

If you would like to mention a role, you will need to run ``[p]bdset rolemention true``

**Placeholders:**
    - ``{name}`` - the user's name
    - ``{mention}`` - an @ mention of the user
    - ``{new_age}`` - the user's new age

    All the placeholders are optional.

**Examples:**
    - ``[p]bdset msgwithyear {mention} has turned {new_age}, happy birthday!``
    - ``[p]bdset msgwithyear {name} is {new_age} today! Happy birthday {mention}!``

.. _birthday-command-bdset-role:

""""""""""
bdset role
""""""""""

**Syntax**

.. code-block:: none

    [p]bdset role <role>

**Description**

Set the role that will be given to the user on their birthday.

You can give the exact name or a mention.

**Example:**
    - ``[p]bdset role @Birthday`` - set the role to @Birthday
    - ``[p]bdset role Birthday`` - set the role to @Birthday without a mention
    - ``[p]bdset role 418058139913063657`` - set the role with an ID

.. _birthday-command-bdset-rolemention:

"""""""""""""""""
bdset rolemention
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]bdset rolemention <value>

**Description**

Choose whether or not to allow role mentions in birthday messages.

By default role mentions are suppressed.

To allow role mentions in the birthday message, run ``[p]bdset rolemention true``.
Disable them with ``[p]bdset rolemention true``

.. _birthday-command-bdset-settings:

""""""""""""""
bdset settings
""""""""""""""

**Syntax**

.. code-block:: none

    [p]bdset settings 

**Description**

View your current settings

.. _birthday-command-bdset-stop:

""""""""""
bdset stop
""""""""""

**Syntax**

.. code-block:: none

    [p]bdset stop 

**Description**

Stop the cog from sending birthday messages and giving roles in the server.

.. _birthday-command-bdset-time:

""""""""""
bdset time
""""""""""

**Syntax**

.. code-block:: none

    [p]bdset time <time>

**Description**

Set the time of day for the birthday message.

Minutes are ignored.

**Examples:**
    - ``[p]bdset time 7:00`` - set the time to 7:45AM UTC
    - ``[p]bdset time 12AM`` - set the time to midnight UTC
    - ``[p]bdset time 3PM`` - set the time to 3:00PM UTC

.. _birthday-command-bdset-zemigrate:

"""""""""""""""
bdset zemigrate
"""""""""""""""

.. note:: |owner-lock|

**Syntax**

.. code-block:: none

    [p]bdset zemigrate 

**Description**

Import data from ZeCogs'/flare's fork of Birthdays cog

.. _birthday-command-birthday:

^^^^^^^^
birthday
^^^^^^^^

**Syntax**

.. code-block:: none

    [p]birthday 

.. tip:: Alias: ``bday``

**Description**

Set and manage your birthday.

.. _birthday-command-birthday-remove:

"""""""""""""""
birthday remove
"""""""""""""""

**Syntax**

.. code-block:: none

    [p]birthday remove 

.. tip:: Aliases: ``birthday delete``, ``birthday del``

**Description**

Remove your birthday.

.. _birthday-command-birthday-set:

""""""""""""
birthday set
""""""""""""

**Syntax**

.. code-block:: none

    [p]birthday set <birthday>

.. tip:: Alias: ``birthday add``

**Description**

Set your birthday.

You can optionally add in the year, if you are happy to share this.

If you use a date in the format xx/xx/xx or xx-xx-xx MM-DD-YYYY is assumed.

**Examples:**
    - ``[p]bday set 24th September``
    - ``[p]bday set 24th Sept 2002``
    - ``[p]bday set 9/24/2002``
    - ``[p]bday set 9-24-2002``
    - ``[p]bday set 9-24``

.. _birthday-command-birthday-upcoming:

"""""""""""""""""
birthday upcoming
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]birthday upcoming [days=7]

**Description**

View upcoming birthdays, defaults to 7 days.

**Examples:**
    - ``[p]birthday upcoming`` - default of 7 days
    - ``[p]birthday upcoming 14`` - 14 days

.. _birthday-command-birthdaydebug-upcoming:

""""""""""""""""""""""
birthdaydebug upcoming
""""""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]birthdaydebug upcoming 
