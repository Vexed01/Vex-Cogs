from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from ..system import System

FRIENDLY_NAMES = {
    "cpu": "CPU",
    "mem": "Memory",
    "sensors": "Sensors",
    "users": "Users",
    "disk": "Disk",
    "proc": "Processes",
    "net": "Network",
    "uptime": "Uptime",
    "red": "Red",
    "all": "All",
}


class SystemDropdown(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        assert isinstance(self.view, SystemView)
        if self.values[0] in ("all", "proc"):  # takes too long
            await interaction.response.defer(ephemeral=True, thinking=True)
            await interaction.message.edit(
                embed=await self.view.cog_methods[self.values[0]](interaction.channel),
            )
            await interaction.followup.send("Done!")
        else:
            await interaction.response.edit_message(
                embed=await self.view.cog_methods[self.values[0]](interaction.channel),
            )


class SystemView(discord.ui.View):
    def __init__(self, author: discord.User | discord.Member, cog: System, initial_metric: str):
        super().__init__()

        self.author = author

        self.cog_methods = {
            "cpu": cog.prep_cpu_msg,
            "mem": cog.prep_mem_msg,
            "sensors": cog.prep_sensors_msg,
            "users": cog.prep_users_msg,
            "disk": cog.prep_disk_msg,
            "proc": cog.prep_proc_msg,
            "net": cog.prep_net_msg,
            "uptime": cog.prep_uptime_msg,
            "red": cog.prep_red_msg,
            "all": cog.prep_all_msg,
        }

        options = []
        for metric, friendly in FRIENDLY_NAMES.items():
            if sys.platform != "linux" and metric == "sensors":
                continue
            options.append(
                discord.SelectOption(
                    label=friendly,
                    value=metric,
                )
            )

        self.add_item(SystemDropdown(options=options, placeholder="Change metric"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                "You are not authorized to interact with this.", ephemeral=True
            )
            return False
        return True
