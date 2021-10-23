import asyncio
import logging
from time import monotonic
from typing import Dict, List

import aiohttp
from aiohttp.client_exceptions import ClientOSError
from vexcogutils.loop import VexLoop

from status.core import FEEDS, SERVICE_LITERAL, TYPES_LITERAL
from status.core.abc import MixinMeta
from status.objects import IncidentData, SendCache, Update

from .processfeed import process_json
from .sendupdate import SendUpdate

_log = logging.getLogger("red.vex.status.updatechecker")


class StatusLoop(MixinMeta):
    """Loop for checking for updates."""

    def __init__(self) -> None:
        self.etags: Dict[str, str] = {}

        self.loop_meta = VexLoop("Status Loop", 120.0)
        self.loop = self.bot.loop.create_task(self.status_loop())

    async def status_loop(self):
        while not self.ready:
            await asyncio.sleep(0.1)

        await asyncio.sleep(1)

        while True:
            self.loop_meta.iter_start()
            _log.debug("Update loop started.")
            if not self.used_feeds.get_list():
                return _log.debug("Nothing to do - no channels have registered for auto updates.")
            start = monotonic()

            try:
                await asyncio.wait_for(self._check_for_updates(), timeout=245)  # 4 min and a bit

                self.loop_meta.iter_finish()
            except asyncio.TimeoutError as e:
                self.loop_meta.iter_error(e)
                _log.warning(
                    "Update checking timed out after 4 minutes. If this happens a lot contact "
                    "Vexed."
                )
            except Exception as e:
                _log.error(
                    "Unable to check and send updates. Some services were likely missed. The "
                    "might be picked up on the next loop. You may want to report this to Vexed.",
                    exc_info=e,
                )
            end = monotonic()
            total = round(end - start, 1)

            _log.debug(f"Update loop finished in {total}s.")

            self.actually_send = True

            await self.loop_meta.sleep_until_next()

    async def _check_for_updates(self) -> None:
        # ############################ INCIDENTS ############################
        for service in self.used_feeds.get_list():
            try:
                resp_json, new_etag, status = await self.statusapi.incidents(
                    FEEDS[service]["id"], self.etags.get(f"incidents-{service}", "")
                )
            except asyncio.TimeoutError:
                _log.warning(
                    f"Timeout checking {service}. Any missed updates will be caught on the next "
                    "loop."
                )
                continue
            except (aiohttp.ClientError, ClientOSError):
                _log.warning(
                    f"Unable to check {service}. Any missed updates will be caught on the next "
                    "loop."
                )
                continue
            except Exception:  # want to catch everything and anything
                _log.error(f"Something unexpected went wrong checking {service}.", exc_info=True)
                continue

            if status == 304:
                _log.debug(f"Incidents: no update for {service} - 304")
                self.last_checked.update_time(service)
            elif status == 200:
                _log.debug(f"Incidents: update detected for {service} - 200")
                self.etags[f"incidents-{service}"] = new_etag
                # dont need to update checked time as above because _maybe_send_update does it
                await self._maybe_send_update(resp_json, service, "incidents")
            elif str(status)[0] == "5":
                _log.info(
                    f"I was unable to get an update for {service} due to problems on their side. "
                    f"(HTTP error {status})"
                )
            else:
                _log.warning(
                    f"Unexpected status code received from {service}: {status}. Please report "
                    "this to Vexed."
                )

        # ############################ SCHEDULED ############################
        for service in self.used_feeds.get_list():
            try:
                resp_json, new_etag, status = await self.statusapi.scheduled_maintenance(
                    FEEDS[service]["id"], self.etags.get(f"scheduled-{service}", "")
                )
            except asyncio.TimeoutError:
                _log.warning(
                    f"Timeout checking {service}. Any missed updates will be caught on the next "
                    "loop."
                )
                continue
            except (aiohttp.ClientError, ClientOSError):
                _log.warning(
                    f"Unable to check {service}. Any missed updates will be caught on the next "
                    "loop."
                )
                continue
            except Exception:  # want to catch everything and anything
                _log.error(f"Something unexpected went wrong checking {service}.", exc_info=True)
                continue

            if status == 304:
                _log.debug(f"Scheduled: no update for {service} - 304")
                self.last_checked.update_time(service)
            elif status == 200:
                _log.debug(f"Scheduled: update detected for {service} - 200")
                self.etags[f"scheduled-{service}"] = new_etag
                # dont need to update checked time as above because _maybe_send_update does it
                await self._maybe_send_update(resp_json, service, "scheduled")
            elif str(status)[0] == "5":
                _log.info(
                    f"I was unable to get an update for {service} due to problems on their side. "
                    f"(HTTP error {status})"
                )
            else:
                _log.warning(
                    f"Unexpected status code received from {service}: {status}. Please report "
                    "this to Vexed."
                )

    async def _maybe_send_update(
        self, resp_json: dict, service: SERVICE_LITERAL, type: TYPES_LITERAL
    ) -> None:
        real = await self._check_real_update(process_json(resp_json, type), service)

        if not real:
            return _log.debug(f"Ghost status update for {service} ({type}) detected.")

        # skip just after migration
        if not self.actually_send:
            return

        if len(real) > 3:
            real = real[:3]  # latest 3
            _log.warning(f"Lots of updates detected for {service}. I will only send the latest 3.")

        for update in real:
            channels = await self.config_wrapper.get_channels(service)
            sendcache = SendCache(update, service)
            await SendUpdate(
                bot=self.bot,
                config_wrapper=self.config_wrapper,
                update=update,
                service=service,
                sendcache=sendcache,
            ).send(channels)

            await asyncio.sleep(5)
            # this loop normally only runs once
            # this sleep will ensure there are no issues with channel webhook ratelimits if lots
            # are being sent for whatever reason. eg when i break stuff locally.

    async def _check_real_update(
        self, incidentdata_list: List[IncidentData], service: str
    ) -> List[Update]:
        stored_ids: list = await self.config.old_ids()
        valid_updates: List[Update] = []
        for incidentdata in incidentdata_list:
            new_fields = []
            for field in incidentdata.fields:
                if field.update_id not in stored_ids:
                    _log.debug(
                        f"New field detected with ID {field.update_id} on incident "
                        f"{incidentdata.incident_id}"
                    )
                    stored_ids.append(field.update_id)
                    new_fields.append(field)

            if new_fields:
                valid_updates.append(Update(incidentdata, new_fields))

        if valid_updates:
            await self.config.old_ids.set(stored_ids)
            await self.config_wrapper.update_incidents(service, valid_updates[0].incidentdata)
            # update_incidents will update the checked time
        else:
            self.last_checked.update_time(service)

        return valid_updates
