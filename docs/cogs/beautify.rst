.. _beautify:

========
Beautify
========

This is the cog guide for the beautify cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _beautify-usage:

-----
Usage
-----

Beautify and minify JSON.

This cog has two commands, ``[p]beautify`` and ``[p]minify``. Both of which behave in similar ways.

They are very flexible and accept inputs in many ways,
for example replies or uploading - or just simply putting it after the command.


.. _beautify-commands:

--------
Commands
--------

.. _beautify-command-beautify:

^^^^^^^^
beautify
^^^^^^^^

**Syntax**

.. code-block:: none

    [p]beautify [data]

**Description**

Beautify some JSON.

This command accepts it in a few forms.

1. Upload the JSON as a file (it can be .txt or .json)
​ ​ ​ ​ - Note that if you upload multiple files I will only scan the first one
2. Paste the JSON in the command
​ ​ ​ ​ - You send it raw, in inline code or a codeblock
​3. Reply to a message with JSON
​ ​ ​ ​ - I will search for attachments and any codeblocks in the message

**Examples:**
    - ``[p]beautify {"1": "One", "2": "Two"}``
    - ``[p]beautify`` (with file uploaded)
    - ``[p]beautify`` (while replying to a messsage)

.. _beautify-command-minify:

^^^^^^
minify
^^^^^^

**Syntax**

.. code-block:: none

    [p]minify [data]

**Description**

Minify some JSON.

This command accepts it in a few forms.

1. Upload the JSON as a file (it can be .txt or .json)
​ ​ ​ ​ - Note that if you upload multiple files I will only scan the first one
2. Paste the JSON in the command
​ ​ ​ ​ - You send it raw, in inline code or a codeblock
​3. Reply to a message with JSON
​ ​ ​ ​ - I will search for attachments and any codeblocks in the message

**Examples:**
    - ``[p]minify {"1": "One", "2": "Two"}``
    - ``[p]minify`` (with file uploaded)
    - ``[p]minify`` (while replying to a messsage)
