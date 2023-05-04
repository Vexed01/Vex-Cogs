from __future__ import annotations

import datetime
from dataclasses import dataclass
from math import ceil

import pandas as pd
from redbot.core.utils.chat_formatting import humanize_timedelta

from .abc import MixinMeta
from .consts import SECONDS_IN_DAY
from .vexutils import get_vex_logger

log = get_vex_logger(__name__)


def round_up_to_min(num: float):
    return ceil(num / 60.0) * 60


@dataclass
class UptimeData:
    total_secs_connected: float
    total_secs_loaded: float

    daily_cog_loaded_data: pd.Series[float]
    daily_connected_data: pd.Series[float]

    seconds_data_collected: float

    first_load: datetime.datetime

    expected_index: pd.DatetimeIndex

    @property
    def downtime(self) -> str:
        """Get complete downtime for selected timeframe"""
        return (
            humanize_timedelta(
                seconds=round_up_to_min(self.seconds_data_collected - self.total_secs_connected)
            )
            or "none"
        )

    def date_downtime(self, date: pd.Timestamp) -> str:
        """Get complete downtime for selected date"""
        return (
            humanize_timedelta(
                seconds=round_up_to_min(SECONDS_IN_DAY - self.daily_connected_data[date])
            )
            or "none"
        )

    @property
    def net_downtime(self) -> str:
        """Get network downtime for selected timeframe"""
        return (
            humanize_timedelta(
                seconds=round_up_to_min(self.total_secs_loaded - self.total_secs_connected)
            )
            or "none"
        )

    def date_net_downtime(self, date: pd.Timestamp) -> str:
        """Get network downtime for selected timeframe"""
        return (
            humanize_timedelta(
                seconds=round_up_to_min(
                    self.daily_cog_loaded_data[date] - self.daily_connected_data[date]
                )
            )
            or "none"
        )

    @property
    def cog_uptime(self) -> str:
        """Percentage of time cog was loaded for selected timeframe"""
        return format(
            round((self.total_secs_loaded / self.seconds_data_collected) * 100, 2), ".2f"
        )

    @property
    def connected_uptime(self) -> str:
        """Percentage of time cog detected bot was online"""
        return format(
            round((self.total_secs_connected / self.seconds_data_collected) * 100, 2), ".2f"
        )

    # for these two below no need to copy because object is single use
    def daily_connected_percentages(self) -> pd.Series:
        midnight = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new = self.daily_connected_data
        for date in self.expected_index:
            if date == midnight:
                continue
            new[date] = format(
                round((self.daily_connected_data[date] / SECONDS_IN_DAY) * 100, 2), ".2f"
            )
        try:
            del new[midnight]
        except KeyError:  # dunno how this could happen but it did once
            pass
        return new.astype(float)

    def daily_cog_loaded_percentages(self) -> pd.Series:
        midnight = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new = self.daily_cog_loaded_data.copy()
        for date in self.expected_index:
            if date == midnight:
                continue
            new[date] = format(
                round((self.daily_cog_loaded_data[date] / SECONDS_IN_DAY) * 100, 2), ".2f"
            )
        del new[midnight]
        return new.astype(float)


class Utils(MixinMeta):
    async def get_data(self, num_days: int) -> UptimeData:
        await self.ready.wait()

        now = datetime.datetime.utcnow()
        if self.main_loop_meta is None or self.main_loop_meta.next_iter is None:
            until_next = 0.0
        else:
            until_next = (
                self.main_loop_meta.next_iter - datetime.datetime.utcnow()
            ).total_seconds()  # assume up to now was up because the command was invoked

        seconds_cog_loaded = 60 - until_next
        seconds_connected = 60 - until_next

        ts_cl = self.cog_loaded_cache.copy(deep=True)
        ts_con = self.connected_cache.copy(deep=True)
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        expected_index = pd.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today(),
            normalize=True,
        )

        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_since_midnight = float((now - midnight).total_seconds())

        log.trace(
            "data filter things: %s",
            {
                "num_days": num_days,
                "now": now,
                "midnight": midnight,
                "seconds_since_midnight": seconds_since_midnight,
                "seconds_cog_loaded": seconds_cog_loaded,
                "seconds_connected": seconds_connected,
                "expected_index": expected_index,
                "conf_first_loaded": conf_first_loaded,
            },
        )

        if len(expected_index) >= num_days:  # need to cut down from days collected
            expected_index = expected_index[-(num_days):]
            seconds_data_collected = float(
                (SECONDS_IN_DAY * (num_days - 1)) + seconds_since_midnight
            )
        else:  # need to use data for all days collected
            if conf_first_loaded > midnight:  # cog was first loaded today
                seconds_data_collected = (now - conf_first_loaded).total_seconds()
                expected_index = pd.date_range(
                    start=conf_first_loaded,
                    end=datetime.datetime.today(),
                    normalize=True,
                )
            else:
                seconds_data_collected = float((len(expected_index) - 1) * SECONDS_IN_DAY)
                seconds_data_collected += seconds_since_midnight

        ts_cl: pd.Series = ts_cl.reindex(expected_index)  # type: ignore
        ts_con: pd.Series = ts_con.reindex(expected_index)  # type: ignore
        seconds_cog_loaded += ts_cl.sum()
        seconds_connected += ts_con.sum()

        # if downtime is under the loop frequency we can just assume it's full uptime... this
        # mainly fixes irregularities near first load
        if seconds_data_collected - seconds_cog_loaded <= 60:  # 60 second loop
            seconds_cog_loaded = seconds_data_collected
        if (
            seconds_data_collected - seconds_connected <= 60
        ):  # for my my experience heartbeats are ~41 secs
            seconds_connected = seconds_data_collected

        return UptimeData(
            total_secs_connected=seconds_connected,
            total_secs_loaded=seconds_cog_loaded,
            daily_cog_loaded_data=ts_cl,
            daily_connected_data=ts_con,
            seconds_data_collected=seconds_data_collected,
            first_load=conf_first_loaded,
            expected_index=expected_index,  # type:ignore
        )
