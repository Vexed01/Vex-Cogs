.. _googletrends:

============
GoogleTrends
============

This is the cog guide for the googletrends cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _googletrends-usage:

-----
Usage
-----

Find what the world is searching, right from Discord.

Please note that there is no Google Trends API, so this is a web scraper and may break at
any time.


.. _googletrends-commands:

--------
Commands
--------

.. _googletrends-command-trends:

^^^^^^
trends
^^^^^^

**Syntax**

.. code-block:: none

    [p]trends [timeframe=7d] [geo=world] <query...>

**Description**

Find what the world is searching, right from Discord.

**Get started with ``[p]trends discord`` for a basic example!**

**Optional**

``timeframe``:
    You can specify either the long (eg ``4hours``) or short (``eg 4h``) version of the
    timeframes. All other values not listed below are invalid.

    ``hour``/``1h``
    ``4hours``/``4h``
    ``day``/``1d``
    ``week``/``7d``
    ``month``/``1m``
    ``3months``/``3m``
    ``12months``/``12m``
    ``5years``/``5y``
    ``all``

``geo``:
    Defaults to ``world``
    You can specify a two-letter geographic code, such as ``US``, ``GB`` or ``FR``.
    Sometimes, you can also add a sub-region. See
    https://go.vexcodes.com/trends_geo for a list.

**Required**

``trends``:
    Whatever you want! You can add multiple trends, and separate them with a space.
    If your trend has spaces in it, you can use ``+`` instead of a space or enclose it
    in quotes, for example ``Card games`` to ``Card+games`` or ``"Card games"``.

**Examples:**

``trends discord``
    The simple one! Trends for Discord, 7 days, worldwide
- ``trends 1d US discord twitter youtube``
    1 day, United Stats searching for Discord, Twitter and YouTube
- ``trends 1y COVID-19``
    Trend for COVID-19 in the last year in the world
- ``trends all GB discord``
    Trend for Discord in the United Kingdom for all time
- ``trends all US-NY "Donald Trump" "Joe Biden"``
    A trend with spaces - Donald Trump and Joe Biden in New York State for all time

.. _googletrends-command-trendsexamples:

^^^^^^^^^^^^^^
trendsexamples
^^^^^^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]trendsexamples 

**Description**

These are some examples of how to use the ``[p]trends`` command,
for details see ``[p]help trends``
