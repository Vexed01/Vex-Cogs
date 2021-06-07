.. _madtranslate:

============
MadTranslate
============

This is the cog guide for the madtranslate cog. You will
find detailed docs about usage and commands.

``[p]`` is considered as your prefix.

.. note::

    To use this cog, you will need to install and load it.

    See the :ref:`getting_started` page.

.. _madtranslate-usage:

-----
Usage
-----

Translate things into lots of languages then back to English!

This will defiantly have some funny moments... Take everything with a pinch of salt!


.. _madtranslate-commands:

--------
Commands
--------

.. _madtranslate-command-madtranslate:

^^^^^^^^^^^^
madtranslate
^^^^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]madtranslate [count=15] <text_to_translate>

.. tip:: Aliases: ``mtranslate``, ``mtrans``

**Description**

Translate something into lots of languages, then back to English!

**Examples:**
    - ``[p]mtrans This is a sentence.``
    - ``[p]mtrans 25 Here's another one.``

At the bottom of the output embed is a count-seed pair. You can use this with
the ``mtransseed`` command to use the same language set.

.. _madtranslate-command-mtransseed:

^^^^^^^^^^
mtransseed
^^^^^^^^^^

**Syntax**

.. code-block:: none

    [p]mtransseed <count_seed> <text_to_translate>

**Description**

Use a count-seed pair to (hopefully) get reproducible results.

They may be unreproducible if Google Translate changes its translations.

The count-seed pair is obtained from the main command, ``mtrans``, in the embed footer.

**Examples:**
    - ``[p]mtrans 15-111111 This is a sentence.``
    - ``[p]mtrans 25-000000 Here's another one.``
