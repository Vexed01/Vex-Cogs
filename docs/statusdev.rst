.. _statusdev:

======
Status
======

The status cog has two events you can listen to, ``on_vexed_status_update`` and
``on_vexed_status_channel_send``.

``status_channel_send`` is fired in quick succession, espscially on larger bots with
lots of channels added, so you shouldn't do anything expensive. ``status_channel_send``
is dispatched after a successful channel send.

``status_update`` is dispatched with the channels the cog intends to send updates to when
an update has been confirmed as a non-ghost update.

There is a guaranteed delay of 1 second between ``status_update`` and the first
``status_channel_send`` to allow you to perform an expensive process (eg get data
from config) and then cache the result for the when ``status_channel_send`` despatches
for each channel so you get the timing correct and you can guarantee it was sent.

Though this is incredibly unlikely, the cog will cancel sending updates (and the subsequent
``status_channel_send``) if it lasts longer than 1 minute and 50 seconds after
``status_update`` the update was detected.

Note that ``status_update`` will not trigger if no channels are subscribed to service -
the cog only checks feeds that have channels subscribed to it.

In terms of testing, the ``devforcestatus`` (alias ``dfs``) command can be used for this.
It simulates an actual/organic update as closely as possible so sends to all registered
channels. The ``force`` parameter will be ``True`` in such cases.


***************
Event Reference
***************

.. function:: on_vexed_status_update(feed, fp_data, service, channels, force)

    This event triggers before updates are sent to channels. See above for details.

    :type feed: :class:`dict`
    :param feed: A fully parsed dictionary with individual updates in the incident
        split up.

        .. note::
            The time the ``time`` key should be a datetime object but it could
            be something else. Make sure you handle this.
        .. note::
            Some feeds only supply the latest update. See the file-level const
            ``AVALIBLE_MODES`` in ``status.py``.
        .. note::
            The majority of updates are in the incorrect order in the ``field`` key.
            They will need reversing if you are using this key. See file-level const
            ``DONT_REVERSE`` in ``status.py`` for ones that don't need it.
    :type fp_data: :class:`FeedParserDict`
    :param fp_data: The raw data from feedparser. The above ``feed`` is reccomended
        where possible.
    :type service: :class:`str`
    :param service: The name of the service, in lower case. Guaranteed to be on of
        the keys in the file-level consts of ``status.py``, though new services are
        being added over time so don't copy-paste and expect it to be one of them.
    :type channels: :class:`dict`
    :param channels: A dict with the keys as channel IDs and the values as a nested
        dict contaning the settings for that channel.
    :type force: :class`bool`
    :param force: Whether or not the update was forced to update with
        ``devforcestatus``/``dfs``

.. function:: on_vexed_status_channel_send(feed, service, channel, webhook, embed)

    This is has similarties and differnces to the above event, mainly that it has less
    data and dispatches after an update was successfully sent to a specific channel.
    See above info at the top of this page for details.

    :type feed: :class:`dict`
    :param feed: A fully parsed dictionary with individual updates in the incident
        split up.

        .. note::
            The time the ``time`` key should be a datetime object but it could
            be something else. Make sure you handle this.
        .. note::
            Some feeds only supply the latest update. See the file-level const
            ``AVALIBLE_MODES`` in ``status.py``.
        .. note::
            The majority of updates are in the incorrect order in the ``field`` key.
            They will need reversing if you are using this key. See file-level const
            ``DONT_REVERSE`` in ``status.py`` for ones that don't need it.
    :type service: :class:`str`
    :param service: The name of the service, in lower case. Guaranteed to be on of
        the keys in the file-level consts of ``status.py``, though new services are
        being added over time so don't copy-paste and expect it to be one of them.
    :type channel: :class:`discord.TextChannel`
    :param channel: The discord.TextChannel object the update was successfully sent to.
    :type webhook: :class:`bool`
    :param webhook: Whether or not the update was sent as a webhook.
    :type embed: :class:`bool`
    :param embed: Whether or not the update was sent as an embed. Will always be ``True``
        if ``webhook`` is ``True``.

