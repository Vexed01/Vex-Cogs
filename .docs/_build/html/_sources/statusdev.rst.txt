.. _statusdev:

=============
Status Events
=============

The status cog has two events you can listen to, ``on_vexed_status_update`` and
``on_vexed_status_channel_send``.

``status_channel_send`` is fired in quick succession, especially on larger bots with
lots of channels added, so you shouldn't do anything expensive. ``status_channel_send``
is dispatched after a successful channel send, so it won't be dispatched if the bot
couldn't send for whatever reason.

``status_update`` is dispatched with the channels the cog intends to send updates to when
an update has been confirmed as a non-ghost update.

There is a guaranteed delay of 1 second between ``status_update`` and the first
``status_channel_send`` to allow you to perform an expensive process (or avoid repeated
config calls for each dispatch) and then cache the result for the when ``status_channel_send``
dispatches for each channel so you get the timing correct and you can guarantee it was sent.

Though this is incredibly unlikely, the cog will cancel sending updates (and the subsequent
``status_channel_send``) if it lasts longer than 4 minutes after
it started that check for updates. Note multiple services' updates may be included in this
time.

The events are linear. ``on_status_update`` guarantees the next ``status_channel_send`` will be
the same update.

.. note::
    If you are using this cog/event to get a parsed update to send yourself, note that
    ``status_update`` will not trigger if no channels are subscribed to the service -
    the cog only checks feeds that have channels subscribed to it.

.. tip::
    For testing, the ``statusdev checkfeed`` (alias ``statusdev cf``) command can be used.
    It will send the latest incident and scheduled maintenance for the service provided to
    the current channel, with the ``force`` parameter being ``True``.

    You can also use ``statusdev forcestatus`` (alias ``statusdev fs``) which will send the
    latest incident to ALL channels in ALL servers that recieve that service's incidents.

*******
Example
*******

.. code-block:: python

    @commands.Cog.listener()
    async def on_vexed_status_update(self, **_kwargs):
        data = await self.config.all_channels()  # get you data from config here
        self.data_cache = data

    @commands.Cog.listener()
    async def on_vexed_status_channel_send(self, *, service, channel_data, **_kwargs):
        data = self.data_cache.get(channel_data.channel.id)
        # then get it back here for each channel send to reduce config calls,
        # esp on larger bots

        if data is None:
            return

        mention_ids = data["user_mentions"].get(service)
        # if you registered in config as user_mentions
        if mention_ids is None:
            return

        mention_ids = [f"<@{id}>" for id in mention_ids]
        await channel_data.channel.send(humanize_list(mention_ids))


***************
Event Reference
***************

.. function:: on_vexed_status_update(update, service, channels, force)

    This event triggers before updates are sent to channels. See above for details.

    :type update: :class:`Update`
    :param update: The main class with the update information, including what was sent
        and the settings it was sent with. It has subclasses in the attributes - see
        below `Custom Objects`_.
    :type service: :class:`str`
    :param service: The name of the service, in lower case. Guaranteed to be on of
        the keys in the file-level consts of ``status.py``, though new services are
        being added over time so don't copy-paste and expect it to be one of them.
    :type channels: :class:`dict`
    :param channels: A dict with the keys as channel IDs and the values as a nested
        dict containing the settings for that channel.
    :type force: :class:`bool`
    :param force: Whether or not the update was forced to update with
        ``statusdev checkfeed``/``statusdev cf``

.. function:: on_vexed_status_channel_send(update, service, channel_data, force)

    This is has similarities to the above event, mainly that it dispatches after an
    update was successfully sent to a specific channel. See above info at the top of
    this page for details.

    :type update: :class:`Update`
    :param update: The main class with the update information, including what was sent
        and the settings it was sent with. It has subclasses - see below `Custom Objects`_.
    :type service: :class:`str`
    :param service: The name of the service, in lower case. Guaranteed to be on of
        the keys in the file-level consts of ``status.py``, though new services are
        being added over time so don't copy-paste and expect it to be one of them.
    :type channel_data: :class:`ChannelData`
    :param channel_data: The channel it was sent to and the associated settings. It has
        subclasses in the attributes - see below `Custom Objects`_.
    :type force: :class:`bool`
    :param force: Whether or not the update was forced to update with
        ``statusdev checkfeed``/``statusdev cf``


**************
Custom Objects
**************

-----------
ChannelData
-----------

``objects/channel.py`` (ignore the custom errors in this file) This object has all the settings that
the update was sent with.

**Attributes**

| **channel** (``discord.TextChannel``) – Idk, this might just be the channel the update was sent to.
| **mode** (``str``) – The mode the update was sent as.
| **webhook** (``bool``) – Whether or not it was sent as a webhook.
| **edit_id** (``Dict[str, int]``) – I cba to explain this, you don't need to know.
| **embed** (``bool``) – Whether or not it was sent as an embed.

------
Update
------

``objects/incidentdata.py`` This is a base object from which the two below are nested in.

**Attributes**

| **incidentdata** (``incidentdata``) – The feed data from which the update was sent. See below.
| **new_fields** (``List[UpdateField]``) – A list of new fields since the service was last checked. Usually 1.

------------
incidentdata
------------

``objects/incidentdata.py`` This is present in the ``incidentdata`` attribute of the ``Update`` object.

**Attributes**

| **fields** (``List[UpdateField]``) – A list containing UpdateField objects
| **title** (``str``) – The title of the incident
| **time**: A datetime object, or if it was unable to parse it then ``discord.Embed.Empty``
| **link** (``str``) – The incident link.
| **actual_time**: A datetime object, or if it was unable to parse it then ``discord.Embed.Empty``
| **description** (``str`` | None) – Exclusively used for when a scheduled incident is being sent.
| **incident_id** (``str``) – The incident's unique ID.
| **scheduled_for**: If the incident sent was scheduled, this is when the event starts/started. Could be ``discord.Embed.Empty``

**Methods**

| **to_dict()** – Get a dict of the data held in the object
| **get_update_ids()** – Get the group IDs. These are unique and represent each update. See UpdateField for more information

-----------
UpdateField
-----------

``objects/incidentdata.py`` This is present in the ``fields`` attribute of the above ``incidentdata`` object and the ``new_fields`` attribute
of the ``Update`` object.

**Attributes**

| **name** (``str``) – The name of the field
| **value** (``str``) – The value of the field
| **update_id** (``str``) – The group ID of the field. These are unique unless the field was split up to accommodate embed limits
