.. _covidgraph:

==========
CovidGraph
==========

This is the cog guide for the covidgraph cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _covidgraph-usage:

-----
Usage
-----

Get COVID-19 graphs.


.. _covidgraph-commands:

--------
Commands
--------

.. _covidgraph-command-covidgraph:

^^^^^^^^^^
covidgraph
^^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]covidgraph 

**Description**

Get graphs of COVID-19 data.

.. _covidgraph-command-covidgraph-cases:

""""""""""""""""
covidgraph cases
""""""""""""""""

**Syntax**

.. code-block:: none

    [p]covidgraph cases [days] <country>

.. tip:: Alias: ``covidgraph c``

**Description**

Get the number of confirmed cases in a country.

You can optionally specify the number of days to get data for,
otherwise it will be all-time.

``country`` can also be ``world`` to get the worldwide data.

**Examples:**
    - ``[p]covidgraph cases US`` - All time data for the US
    - ``[p]covidgraph cases 7 US`` - Last 7 days for the US
    - ``[p]covidgraph cases world`` - Worldwide data

.. _covidgraph-command-covidgraph-deaths:

"""""""""""""""""
covidgraph deaths
"""""""""""""""""

**Syntax**

.. code-block:: none

    [p]covidgraph deaths [days] <country>

.. tip:: Alias: ``covidgraph d``

**Description**

Get the number of deaths in a country.

You can optionally specify the number of days to get data for,
otherwise it will be all-time.

``country`` can also be ``world`` to get the worldwide data.

**Examples:**
    - ``[p]covidgraph deaths US`` - All time data for the US
    - ``[p]covidgraph deaths 7 US`` - Last 7 days for the US
    - ``[p]covidgraph deaths world`` - Worldwide data

.. _covidgraph-command-covidgraph-vaccines:

"""""""""""""""""""
covidgraph vaccines
"""""""""""""""""""

**Syntax**

.. code-block:: none

    [p]covidgraph vaccines [days] <country>

.. tip:: Alias: ``covidgraph v``

**Description**

Get the number of vaccine doses administered in a country.

You can optionally specify the number of days to get data for,
otherwise it will be all-time.

``country`` can also be ``world`` to get the worldwide data.

**Examples:**
    - ``[p]covidgraph vaccines US`` - All time data for the US
    - ``[p]covidgraph vaccines 7 US`` - Last 7 days for the US
    - ``[p]covidgraph vaccines world`` - Worldwide data
