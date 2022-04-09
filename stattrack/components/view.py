from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Iterable

import discord
from redbot.core.utils.chat_formatting import humanize_timedelta

from ..consts import ALL_CHARTS, TRACE_FRIENDLY_NAMES

if TYPE_CHECKING:
    from stattrack.commands import StatTrackCommands


class ChangeChartDropdown(discord.ui.Select):
    def __init__(self, charts: list[discord.SelectOption]) -> None:
        super().__init__(placeholder="Change chart", options=charts)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        assert isinstance(self.view, StatTrackView)

        chart = self.values[0]

        self.view.stop()
        await self.view.comclass.all_in_one(
            ctx=interaction.message,
            chart=chart,
            delta=self.view.delta,
            label=ALL_CHARTS[chart]["valid_metrics"],
            title=ALL_CHARTS[chart]["title"],
            ylabel=ALL_CHARTS[chart]["ylabel"],
            author=self.view.author,
            more_options=ALL_CHARTS[chart]["more_options"],
            do_average=ALL_CHARTS[chart]["do_average"],
            show_total=ALL_CHARTS[chart]["show_total"],
            status_colours=ALL_CHARTS[chart]["status_colours"],
        )

        await interaction.followup.send("Edited")


class ChangeMetricsDropdown(discord.ui.Select):
    def __init__(self, metrics: list[discord.SelectOption]) -> None:
        super().__init__(placeholder="Change metrics", options=metrics, max_values=len(metrics))

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        assert isinstance(self.view, StatTrackView)

        self.view.stop()

        chart = self.view.chart

        await self.view.comclass.all_in_one(
            ctx=interaction.message,
            chart=chart,
            delta=self.view.delta,
            label=self.values,
            title=ALL_CHARTS[chart]["title"],
            ylabel=ALL_CHARTS[chart]["ylabel"],
            author=self.view.author,
            more_options=ALL_CHARTS[chart]["more_options"],
            do_average=ALL_CHARTS[chart]["do_average"],
            show_total=ALL_CHARTS[chart]["show_total"],
            status_colours=ALL_CHARTS[chart]["status_colours"],
        )

        await interaction.followup.send("Edited")


class ChangeTimespanDropdown(discord.ui.Select):
    DEFAULT_TIMES = {
        "1 hour": timedelta(hours=1),
        "1 day": timedelta(days=1),
        "1 week": timedelta(days=7),
        "1 month": timedelta(days=30),
        "all": timedelta(days=9000),
    }

    def __init__(self, metrics: list[discord.SelectOption]) -> None:
        super().__init__(placeholder="Change timespan", options=metrics)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        assert isinstance(self.view, StatTrackView)

        self.view.stop()

        chart = self.view.chart

        new_delta = timedelta(seconds=float(self.values[0]))

        await self.view.comclass.all_in_one(
            ctx=interaction.message,
            chart=chart,
            delta=new_delta,
            label=self.view.current_metrics,
            title=ALL_CHARTS[chart]["title"],
            ylabel=ALL_CHARTS[chart]["ylabel"],
            author=self.view.author,
            more_options=ALL_CHARTS[chart]["more_options"],
            do_average=ALL_CHARTS[chart]["do_average"],
            show_total=ALL_CHARTS[chart]["show_total"],
            status_colours=ALL_CHARTS[chart]["status_colours"],
        )

        await interaction.followup.send("Edited")


class StatTrackView(discord.ui.View):
    def __init__(
        self,
        *,
        comclass: StatTrackCommands,
        chart: str,
        current_metrics: Iterable[str],
        author: discord.User | discord.Member,
        current_delta: timedelta,
    ) -> None:
        super().__init__()

        self.comclass = comclass
        self.author = author
        self.delta = current_delta

        self.chart = chart
        self.current_metrics = current_metrics

        charts = []
        for chart_name, chart_data in ALL_CHARTS.items():
            if chart_name == chart:
                charts.append(
                    discord.SelectOption(
                        label=chart_data["title"],
                        value=chart_name,
                        default=True,
                    )
                )
            else:
                charts.append(
                    discord.SelectOption(
                        label=chart_data["title"],
                        value=chart_name,
                    )
                )

        self.add_item(ChangeChartDropdown(charts))

        metrics = []
        if len(ALL_CHARTS[chart]["valid_metrics"]) > 1:
            for metric in ALL_CHARTS[chart]["valid_metrics"]:
                if metric in current_metrics:
                    metrics.append(
                        discord.SelectOption(
                            label=TRACE_FRIENDLY_NAMES[metric],
                            value=metric,
                            default=True,
                        )
                    )
                else:
                    metrics.append(
                        discord.SelectOption(
                            label=TRACE_FRIENDLY_NAMES[metric],
                            value=metric,
                        )
                    )

            self.add_item(ChangeMetricsDropdown(metrics))

        deltas = []
        got_current_delta = False
        for human, delta in ChangeTimespanDropdown.DEFAULT_TIMES.items():
            if delta == current_delta:
                deltas.append(
                    discord.SelectOption(
                        label=human,
                        value=str(delta.total_seconds()),
                        default=True,
                    )
                )
                got_current_delta = True
            else:
                deltas.append(
                    discord.SelectOption(
                        label=human,
                        value=str(delta.total_seconds()),
                    )
                )
        if not got_current_delta:
            deltas.append(
                discord.SelectOption(
                    label=humanize_timedelta(timedelta=current_delta),
                    value=str(current_delta.total_seconds()),
                    default=True,
                )
            )

        self.add_item(ChangeTimespanDropdown(deltas))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                "You are not authorized to interact with this.", ephemeral=True
            )
            return False
        return True
